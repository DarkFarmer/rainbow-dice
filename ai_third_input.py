import util
import board_state
import random
import math

def ai_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number):
    """
    Improved AI that:
      1. Considers synergy between missile and melee (shoot + charge).
      2. Values getting onto control points for VP.
      3. Prioritizes finishing off weakened enemies.
      4. Excludes enemies locked in melee from being shot.
      5. Units can charge into existing combats (help allies in melee).
    """
    available_units = [u for u in active_player.units if u.is_alive() and not u.has_activated]
    if not available_units:
        return None

    # Sort units by priority (Highest AP, then units in melee)
    def in_melee(u):
        return any(e.is_alive() and util.distance(u.position, e.position) <= 1 for e in opposing_player.units)
    available_units.sort(key=lambda u: (u.ap_cost, in_melee(u)), reverse=True)

    chosen_unit = available_units[0]

    # If already in melee, fight or disengage
    if chosen_unit.is_locked_in_melee():
        if 'Disengage' in chosen_unit.keywords and chosen_unit_should_disengage(chosen_unit, opposing_player):
            disengage_unit(chosen_unit, active_player)
        else:
            # Attack in melee
            if chosen_unit.melee_engaged_units:
                enemy_target = chosen_unit.melee_engaged_units[0]
                melee_fight(chosen_unit, enemy_target, active_player, battlefield)
        chosen_unit.has_activated = True
        return chosen_unit

    # 10% chance to Regenerate if wounded
    if 'Regenerate' in chosen_unit.keywords and random.random() < 0.1:
        chosen_unit.regenerate()
        chosen_unit.has_activated = True
        return chosen_unit

    # Decide movement
    move_target = decide_move_target(chosen_unit, active_player, opposing_player, battlefield)
    if move_target:
        chosen_unit.position = util.move_towards(chosen_unit.position, move_target, chosen_unit.movement)

    # Attempt a missile attack
    shot_successful = try_missile_attack(chosen_unit, active_player, opposing_player, battlefield)

    # If the target is still alive, or if there are other enemies to charge, attempt it
    # Especially if the unit has decent melee or wants to help an ally in melee
    try_charge(chosen_unit, active_player, opposing_player, battlefield)

    chosen_unit.has_activated = True
    return chosen_unit


def chosen_unit_should_disengage(unit, opposing_player):
    """
    Optional logic to decide if the unit is too weak to stay in melee.
    For now, returns False to encourage more melee.
    """
    return False


def disengage_unit(unit, active_player):
    """
    Unit tries to move away from melee.
    """
    away_position = (unit.position[0] + unit.movement, unit.position[1] + unit.movement)
    unit.position = util.move_towards(unit.position, away_position, unit.movement)
    for enemy in unit.melee_engaged_units[:]:
        enemy.remove_melee_engagement(unit)
        unit.remove_melee_engagement(enemy)


def decide_move_target(chosen_unit, active_player, opposing_player, battlefield):
    """
    Revised priorities:
      1. Move to a control point with nearby enemies (~6") for potential melee + VP.
      2. If strong melee > missile, move near the closest enemy.
      3. Otherwise, pick the nearest CP.
    """
    control_points = battlefield.get_control_points()
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]

    if not control_points and not alive_enemies:
        return None

    # 1. Look for a CP with enemies within ~6" so we can fight on the CP
    cp_enemy_targets = []
    for cp in control_points:
        enemy_count = sum(1 for e in alive_enemies if util.distance((cp.x, cp.y), e.position) <= 6)
        if enemy_count > 0:
            cp_enemy_targets.append(cp)

    if cp_enemy_targets:
        cp_enemy_targets.sort(key=lambda c: util.distance(chosen_unit.position, (c.x, c.y)))
        return (cp_enemy_targets[0].x, cp_enemy_targets[0].y)

    # 2. If we have strong melee dice, move to the nearest enemy
    melee_count = len(chosen_unit.base_melee_attack_dice)
    missile_count = len(chosen_unit.base_missile_attack_dice)
    if melee_count > missile_count and alive_enemies:
        target_enemy = min(alive_enemies, key=lambda e: util.distance(chosen_unit.position, e.position))
        return target_enemy.position

    # 3. Otherwise, go to the nearest control point
    if control_points:
        control_points_sorted = sorted(control_points,
                                       key=lambda cp: util.distance(chosen_unit.position, (cp.x, cp.y)))
        return (control_points_sorted[0].x, control_points_sorted[0].y)

    return None


def try_missile_attack(chosen_unit, active_player, opposing_player, battlefield):
    """
    Attempt a missile attack if target is in range.
    Return True if an attack was made, otherwise False.

    EXCLUDES enemies already locked in melee.
    """
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]
    if not alive_enemies or not chosen_unit.base_missile_attack_dice:
        return False

    # Exclude enemies locked in melee
    free_enemies = [e for e in alive_enemies if not e.is_locked_in_melee()]

    if not free_enemies:
        return False

    # Pick a target in range
    viable_targets = [
        e for e in free_enemies
        if util.distance(chosen_unit.position, e.position) <= chosen_unit.attack_range
        # Also exclude enemies within 1" of active_player's units
        and not any(util.distance(e.position, ally.position) <= 1 
                    for ally in active_player.units if ally.is_alive())
    ]
    if not viable_targets:
        return False

    # If we have allies stuck in melee, try to free them by shooting
    ally_stuck_in_melee = {
        friendly for friendly in active_player.units
        if friendly.is_alive() and friendly.is_locked_in_melee()
    }
    if ally_stuck_in_melee:
        engaged_enemies = [
            e for e in viable_targets
            if any(e in ally.melee_engaged_units for ally in ally_stuck_in_melee)
        ]
        if engaged_enemies:
            enemy_target = random.choice(engaged_enemies)
        else:
            enemy_target = random.choice(viable_targets)
    else:
        enemy_target = random.choice(viable_targets)

    from fight import simulate_fight
    simulate_fight(chosen_unit, enemy_target, active_player, battlefield)
    return True


def try_charge(chosen_unit, active_player, opposing_player, battlefield):
    """
    Attempt to charge into melee, including existing combats to help allies.
    1. Identify enemies in range (<= 12").
    2. Prefer helping allies in melee near control points if possible.
    3. If none found, fallback to finishing off wounded enemies or random target.
    """
    from fight import simulate_fight, melee_favorable

    # 1. Collect valid enemies within 12"
    enemies_in_range = [
        e for e in opposing_player.units
        if e.is_alive() and util.distance(chosen_unit.position, e.position) <= 12
    ]
    if not enemies_in_range:
        return

    # Allies in melee
    ally_in_melee = [ally for ally in active_player.units if ally.is_locked_in_melee()]

    # 2. Gather enemies engaged with our allies
    engaged_enemies = set()
    for ally in ally_in_melee:
        engaged_enemies.update(ally.melee_engaged_units)

    # Filter to those in range
    engaged_enemies = [e for e in engaged_enemies if e in enemies_in_range]

    # If we have engaged enemies, prefer to charge them
    if engaged_enemies:
        # Sort by distance to control points or by how wounded they are
        engaged_enemies.sort(key=lambda e: charge_priority(e, battlefield))
        enemy_target = engaged_enemies[0]
    else:
        # 3. If no engaged enemies, pick from all enemies_in_range, sorted by how wounded + CP distance
        enemies_in_range.sort(key=lambda e: charge_priority(e, battlefield))
        enemy_target = enemies_in_range[0]

    dist = util.distance(chosen_unit.position, enemy_target.position)
    charge_roll = roll_2d6()

    # Overwatch check
    if 'Overwatch' in enemy_target.keywords and not enemy_target.has_activated:
        enemy_target.attack(chosen_unit, 'missile', charging=False, battlefield=battlefield)

    if charge_roll >= dist and melee_favorable(chosen_unit, enemy_target):
        simulate_fight(chosen_unit, enemy_target, active_player, battlefield, 0, 'melee', charging=True)


def charge_priority(enemy, battlefield):
    """
    Ranking function for choosing which enemy to charge:
    - Ratio of remaining models (lower ratio => more wounded => easier kill).
    - Distance to nearest CP (closer => more strategic).
    Returns a tuple for sorting: (ratio, distance_to_cp).
    """
    ratio = enemy.num_models / enemy.initial_num_models
    if battlefield.control_points:
        distance_to_cp = min(
            util.distance(enemy.position, (cp.x, cp.y)) for cp in battlefield.control_points
        )
    else:
        distance_to_cp = 999
    return (ratio, distance_to_cp)


def melee_fight(chosen_unit, enemy_target, active_player, battlefield):
    from fight import simulate_fight
    simulate_fight(chosen_unit, enemy_target, active_player, battlefield, 0, 'melee')


def chosen_unit_should_disengage(unit, opposing_player):
    """ 
    Keep it simple for now: always returns False to promote more melee. 
    A more advanced system could compare HP ratio, etc.
    """
    return False


def find_unit_by_id_or_name(units, identifier):
    try:
        unit_id = int(identifier)
        for u in units:
            if getattr(u, 'id', None) == unit_id:
                return u
        return None
    except ValueError:
        matches = [u for u in units if u.name.lower() == identifier.lower()]
        if len(matches) == 1:
            return matches[0]
        return None


def roll_2d6():
    return random.randint(1, 6) + random.randint(1, 6)
