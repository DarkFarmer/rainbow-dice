import util
import board_state
import random
import math

def ai_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number):
    """
    Improved AI that:
      1. Considers synergy between missile and melee (e.g., shoot + charge).
      2. Values getting onto control points for VP.
      3. Prioritizes finishing off weakened enemies.
    """
    available_units = [u for u in active_player.units if u.is_alive() and not u.has_activated]
    if not available_units:
        return None

    # Sort units by priority (Highest AP, then units in melee)
    def in_melee(u):
        return any(e.is_alive() and util.distance(u.position, e.position) <= 1 for e in opposing_player.units)
    available_units.sort(key=lambda u: (u.ap_cost, in_melee(u)), reverse=True)

    chosen_unit = available_units[0]

    # If in melee, fight or disengage
    if chosen_unit.is_locked_in_melee():
        # Possibly DISENGAGE if heavily outmatched, else fight
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

    # Try a missile attack
    shot_successful = try_missile_attack(chosen_unit, active_player, opposing_player, battlefield)

    # If we have not yet killed the target and are still in range to charge, attempt it
    # We encourage charging if:
    #   - The unit has decent melee dice
    #   - The enemy is either near a control point or is partially wounded
    if shot_successful:  
        # Attempt finishing blow if the target is still alive
        try_charge(chosen_unit, active_player, opposing_player, battlefield)

    chosen_unit.has_activated = True
    return chosen_unit

def chosen_unit_should_disengage(unit, opposing_player):
    """
    Optional logic to decide if the unit is too weak to stay in melee.
    For now, returns False to encourage more melee. 
    If you want to keep some nuance, implement a condition (hp ratio, etc.).
    """
    return False  # We won't auto-disengage often to promote melee.

def disengage_unit(unit, active_player):
    """
    Unit tries to move away from melee. 
    Example code from original:
    """
    away_position = (unit.position[0] + unit.movement, unit.position[1] + unit.movement)
    unit.position = util.move_towards(unit.position, away_position, unit.movement)
    for enemy in unit.melee_engaged_units[:]:
        enemy.remove_melee_engagement(unit)
        unit.remove_melee_engagement(enemy)

def decide_move_target(chosen_unit, active_player, opposing_player, battlefield):
    """
    Revised priorities:
      1. Move to a control point where an enemy is present (so we can fight on the CP).
      2. If the unit has strong melee, prioritize moving near an enemy to enable a future charge.
      3. Otherwise, default to nearest less contested CP.
    """
    control_points = battlefield.get_control_points()
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]

    if not control_points and not alive_enemies:
        return None  # No movement needed if there's no CP or enemy

    # 1. Look for a control point with enemies in ~ 6" range
    #    This ensures we can fight near a CP for points
    cp_enemy_targets = []
    for cp in control_points:
        enemy_count = sum(1 for e in alive_enemies if util.distance((cp.x, cp.y), e.position) <= 6)
        if enemy_count > 0:
            cp_enemy_targets.append(cp)

    if cp_enemy_targets:
        # Pick CP with fewest enemies for a safer approach
        cp_enemy_targets.sort(key=lambda c: (util.distance(chosen_unit.position, (c.x, c.y))))
        best_cp = cp_enemy_targets[0]
        return (best_cp.x, best_cp.y)

    # 2. If we have strong melee dice, prefer heading straight to the nearest enemy
    melee_count = len(chosen_unit.base_melee_attack_dice)
    missile_count = len(chosen_unit.base_missile_attack_dice)
    if melee_count > missile_count and alive_enemies:
        # Move toward the nearest alive enemy
        target_enemy = min(alive_enemies, key=lambda e: util.distance(chosen_unit.position, e.position))
        return target_enemy.position

    # 3. If no immediate synergy with enemy, move to the least-contested CP
    if control_points:
        control_points_sorted = sorted(control_points, 
            key=lambda cp: util.distance(chosen_unit.position, (cp.x, cp.y)))
        return (control_points_sorted[0].x, control_points_sorted[0].y)

    return None

def try_missile_attack(chosen_unit, active_player, opposing_player, battlefield):
    """
    Attempt a missile attack if any target is in range.
    Return True if an attack was made (successful or not), False if no shot occurred.
    """
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]
    if not alive_enemies or len(chosen_unit.base_missile_attack_dice) == 0:
        return False

    # Potentially pick an enemy in range
    viable_targets = [
        e for e in alive_enemies 
        if util.distance(chosen_unit.position, e.position) <= chosen_unit.attack_range
        and not any(util.distance(e.position, ally.position) <= 1 
                    for ally in active_player.units if ally.is_alive())
    ]
    if not viable_targets:
        return False

    # If we have an ally in melee, try to free them by shooting
    ally_stuck_in_melee = {
        friendly for friendly in active_player.units if friendly.is_alive() and 
        friendly.is_locked_in_melee()
    }
    if ally_stuck_in_melee:
        engaged_enemies = [e for e in viable_targets
                           if any(e in ally.melee_engaged_units for ally in ally_stuck_in_melee)]
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
    Attempt to charge an enemy in range (<= 12). 
    Emphasize finishing off wounded enemies, especially near control points.
    """
    from fight import simulate_fight, melee_favorable

    # Find enemies within 12" of chosen_unit
    enemies_in_range = [e for e in opposing_player.units 
                        if e.is_alive() and util.distance(chosen_unit.position, e.position) <= 12]

    if not enemies_in_range:
        return

    # Sort by how wounded the enemy is (more wounded = prime target)
    # or prioritize those near a CP for synergy
    def enemy_priority(e):
        # Combined metric: ratio of remaining models vs. initial, plus proximity to CP
        # Lower ratio = more wounded, we want to finish them.
        ratio = e.num_models / e.initial_num_models
        distance_to_cp = min(
            util.distance(e.position, (cp.x, cp.y)) 
            for cp in battlefield.control_points
        ) if battlefield.control_points else 999
        return (ratio, distance_to_cp)

    enemies_in_range.sort(key=enemy_priority)
    enemy_target = enemies_in_range[0]

    dist = util.distance(chosen_unit.position, enemy_target.position)
    charge_roll = roll_2d6()

    # Overwatch check
    if 'Overwatch' in enemy_target.keywords and not enemy_target.has_activated:
        enemy_target.attack(chosen_unit, 'missile', charging=False, battlefield=battlefield)

    # If roll is high enough and melee_favorable is True, charge into melee
    if charge_roll >= dist and melee_favorable(chosen_unit, enemy_target):
        simulate_fight(chosen_unit, enemy_target, active_player, battlefield, 0, 'melee', charging=True)

def melee_fight(chosen_unit, enemy_target, active_player, battlefield):
    from fight import simulate_fight
    simulate_fight(chosen_unit, enemy_target, active_player, battlefield, 0, 'melee')


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
