import util
import board_state
import random
import math

def ai_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number):
    available_units = [u for u in active_player.units if u.is_alive() and not u.has_activated]
    if not available_units:
        return None

    def in_melee(u):
        return any(e.is_alive() and util.distance(u.position, e.position) <= 1 for e in opposing_player.units)

    # Sort units by priority (Highest AP, then units in melee)
    available_units.sort(key=lambda u: (u.ap_cost, in_melee(u)), reverse=True)

    chosen_unit = available_units[0]

    # Handle if unit is currently in melee
    if chosen_unit.melee_target is not None and 'Disengage' in chosen_unit.keywords:
        # Disengage
        away_position = (chosen_unit.position[0] + chosen_unit.movement, chosen_unit.position[1] + chosen_unit.movement)
        chosen_unit.position = util.move_towards(chosen_unit.position, away_position, chosen_unit.movement)
        if chosen_unit.melee_target:
            chosen_unit.melee_target.melee_target = None
        chosen_unit.melee_target = None
    elif chosen_unit.melee_target is not None:
        # Fight melee
        melee_fight(chosen_unit, chosen_unit.melee_target, active_player)
        chosen_unit.has_activated = True
        return chosen_unit

    # Consider Regenerate
    if 'Regenerate' in chosen_unit.keywords and random.random() < 0.1:
        chosen_unit.regenerate()
        chosen_unit.has_activated = True
        return chosen_unit

    # Determine movement target based on new priorities
    move_target = decide_move_target(chosen_unit, active_player, opposing_player, battlefield)
    if move_target:
        move_distance = chosen_unit.movement
        chosen_unit.position = util.move_towards(chosen_unit.position, move_target, move_distance)

    # Attempt missile attack
    try_missile_attack(chosen_unit, active_player, opposing_player)

    # Attempt charge
    try_charge(chosen_unit, active_player, opposing_player)

    chosen_unit.has_activated = True
    return chosen_unit


def decide_move_target(chosen_unit, active_player, opposing_player, battlefield):
    """
    New Priority:
    1. If unit has stronger melee (more melee dice than missile dice):
       Move towards the nearest enemy that is not currently engaged in melee and attempt to charge.
    2. If unit's missile attack is stronger or equal to melee:
       Move to a control point that has enemies nearby (to shoot them).
    3. If no threatening enemies, just move to the nearest control point.

    'Not engaged' enemy: an enemy that does not have a melee_target and is not within 1" of any friendly unit.
    """
    control_points = battlefield.get_control_points()
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]

    melee_dice_count = len(chosen_unit.base_melee_attack_dice)
    missile_dice_count = len(chosen_unit.base_missile_attack_dice)

    def enemy_presence_at_cp(cp):
        radius = 6
        return sum(1 for e in alive_enemies if util.distance((cp.x, cp.y), e.position) <= radius)

    def is_enemy_engaged(enemy):
        # Enemy engaged if it has a melee_target or is within 1" of any friendly unit
        if enemy.melee_target is not None:
            return True
        # Check proximity to any friendly unit
        if any(util.distance(enemy.position, f.position) <= 1 for f in active_player.units if f.is_alive()):
            return True
        return False

    # 1. Melee preferred: Find a not engaged enemy
    if melee_dice_count > missile_dice_count:
        not_engaged_enemies = [e for e in alive_enemies if not is_enemy_engaged(e)]
        if not_engaged_enemies:
            # Move towards the nearest non-engaged enemy
            target_enemy = min(not_engaged_enemies, key=lambda e: util.distance(chosen_unit.position, e.position))
            return target_enemy.position
        # If no not-engaged enemy found, fall through to next logic

    # 2. Missile preferred or equal: Move to a CP with enemies nearby
    # Only do this if missile >= melee
    if missile_dice_count >= melee_dice_count and control_points and alive_enemies:
        # Find a CP with enemies nearby
        cps_with_enemies = [(cp, enemy_presence_at_cp(cp)) for cp in control_points if enemy_presence_at_cp(cp) > 0]
        if cps_with_enemies:
            # Sort by fewest enemies (safer) then by distance
            cps_with_enemies.sort(key=lambda x: (x[1], util.distance((x[0].x, x[0].y), chosen_unit.position)))
            best_cp = cps_with_enemies[0][0]
            return (best_cp.x, best_cp.y)

    # 3. If no threats, just move to the nearest least contested CP
    if control_points:
        # Sort control points by enemy presence, then by distance
        control_points_sorted = sorted(control_points, key=lambda cp: (enemy_presence_at_cp(cp), util.distance((cp.x, cp.y), chosen_unit.position)))
        best_cp = control_points_sorted[0]
        return (best_cp.x, best_cp.y)

    # If no CPs or enemies, stand still
    return None


def try_missile_attack(chosen_unit, active_player, opposing_player):
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]
    viable_targets = [
        e for e in alive_enemies 
        if util.distance(chosen_unit.position, e.position) <= chosen_unit.attack_range
        and not any(util.distance(e.position, ally.position) <= 1 for ally in active_player.units if ally.is_alive())
    ]
    if viable_targets:
        ally_stuck_in_melee = {
            friendly for friendly in active_player.units if friendly.is_alive() and 
            any(util.distance(friendly.position, ene.position) <= 1 for ene in opposing_player.units if ene.is_alive())
        }
        if ally_stuck_in_melee:
            engaged_enemies = [e for e in viable_targets
                                if any(util.distance(e.position, f.position) <= 1 for f in ally_stuck_in_melee)]
            if engaged_enemies:
                enemy_target = random.choice(engaged_enemies)
            else:
                enemy_target = random.choice(viable_targets)
        else:
            enemy_target = random.choice(viable_targets)

        from fight import simulate_fight
        simulate_fight(chosen_unit, enemy_target, active_player)


def try_charge(chosen_unit, active_player, opposing_player):
    from fight import simulate_fight, melee_favorable

    ally_in_melee = [
        friendly for friendly in active_player.units if friendly.is_alive() and 
        friendly.melee_target is not None
    ]

    enemies_in_range = [e for e in opposing_player.units if e.is_alive() and util.distance(chosen_unit.position, e.position) <= 12]
    if not enemies_in_range:
        return

    # If we have allies in melee, try to charge the enemy that traps them
    if ally_in_melee:
        enemies_trapping_allies = [
            e for e in enemies_in_range 
            if any(util.distance(e.position, f.position) <= 1 for f in ally_in_melee)
        ]
        if enemies_trapping_allies:
            enemy_target = min(enemies_trapping_allies, key=lambda e: util.distance(chosen_unit.position, e.position))
        else:
            enemy_target = min(enemies_in_range, key=lambda e: util.distance(chosen_unit.position, e.position))
    else:
        enemy_target = min(enemies_in_range, key=lambda e: util.distance(chosen_unit.position, e.position))

    dist = util.distance(chosen_unit.position, enemy_target.position)
    charge_roll = roll_2d6()

    # Overwatch check
    if 'Overwatch' in enemy_target.keywords and not enemy_target.has_activated:
        enemy_target.attack(chosen_unit, 'missile', charging=False)

    if charge_roll >= dist and melee_favorable(chosen_unit, enemy_target):
        simulate_fight(chosen_unit, enemy_target, active_player, 0, 'melee', charging=True)
        chosen_unit.melee_target = enemy_target
        enemy_target.melee_target = chosen_unit


def melee_fight(chosen_unit, enemy_target, active_player):
    from fight import simulate_fight
    simulate_fight(chosen_unit, enemy_target, active_player, 0, 'melee')


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
