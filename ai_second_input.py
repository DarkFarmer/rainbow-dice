import util
import board_state
import random
import math

def ai_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number):
    available_units = [u for u in active_player.units if u.is_alive() and not u.has_activated]
    if not available_units:
        return None

    # Sort units by priority:
    # 1. Highest AP first
    # 2. Units currently in melee (so they can free up and shoot/attack again)
    # 3. As a tiebreaker, random or additional heuristics can apply
    # Check if unit is in melee by seeing if any enemy is within 1"
    def in_melee(u):
        return any(e.is_alive() and util.distance(u.position, e.position) <= 1 for e in opposing_player.units)

    available_units.sort(key=lambda u: (u.ap_cost, in_melee(u)), reverse=True)

    chosen_unit = available_units[0]

    if chosen_unit.melee_target is not None and 'Disengage' in chosen_unit.keywords:
        # Unit tries to disengage: move away from enemy before doing anything else
        away_position = (chosen_unit.position[0] + chosen_unit.movement, chosen_unit.position[1] + chosen_unit.movement)
        chosen_unit.position = util.move_towards(chosen_unit.position, away_position, chosen_unit.movement)
        chosen_unit.melee_target.melee_target = None
        chosen_unit.melee_target = None  # now not in melee
    elif chosen_unit.melee_target is not None:
        # No Disengage: fight melee
        melee_fight(chosen_unit, chosen_unit.melee_target, active_player)
        chosen_unit.has_activated = True
        return chosen_unit

    # Consider Regenerate (small chance if wounded)
    if 'Regenerate' in chosen_unit.keywords and random.random() < 0.1:
        chosen_unit.regenerate()
        chosen_unit.has_activated = True
        return chosen_unit

    # Determine movement target
    move_target = decide_move_target(chosen_unit, active_player, opposing_player, battlefield)
    if move_target:
        move_distance = chosen_unit.movement
        chosen_unit.position = util.move_towards(chosen_unit.position, move_target, move_distance)

    # Attempt missile attack
    try_missile_attack(chosen_unit, active_player, opposing_player)

    # Attempt charge, with preference to help units in melee
    try_charge(chosen_unit, active_player, opposing_player)

    chosen_unit.has_activated = True
    return chosen_unit


def decide_move_target(chosen_unit, active_player, opposing_player, battlefield):
    """Decide where the chosen unit should move.
       Preferences:
       1. Move towards a control point that is less contested or unoccupied by enemies.
       2. If no suitable CP, move towards the nearest enemy.
    """
    control_points = battlefield.get_control_points()
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]

    # Helper to measure how contested a CP is: number of enemy units within 6"
    def enemy_presence_at_cp(cp):
        radius = 6
        enemy_count = sum(1 for e in alive_enemies if util.distance((cp.x, cp.y), e.position) <= radius)
        return enemy_count

    # Pick a CP with minimal enemy presence
    if control_points:
        # Sort control points by enemy presence, then by distance to this unit
        control_points_sorted = sorted(control_points, key=lambda cp: (enemy_presence_at_cp(cp), util.distance((cp.x, cp.y), chosen_unit.position)))
        best_cp = control_points_sorted[0]
        # If this CP is reasonably safe (few or no enemies) or if no enemies exist, go there
        if enemy_presence_at_cp(best_cp) < 2 or not alive_enemies:
            return (best_cp.x, best_cp.y)

    # If no good CP or prefer enemies, go for the nearest enemy
    if alive_enemies:
        nearest_enemy = min(alive_enemies, key=lambda e: util.distance(chosen_unit.position, e.position))
        return nearest_enemy.position

    # If no enemies and no CP worth taking, just stand still
    return None


def try_missile_attack(chosen_unit, active_player, opposing_player):
    # Fire at a random valid target if in range and not engaged in melee
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]
    viable_targets = [
        e for e in alive_enemies 
        if util.distance(chosen_unit.position, e.position) <= chosen_unit.attack_range
        and not any(util.distance(e.position, ally.position) <= 1 for ally in active_player.units if ally.is_alive())
    ]
    if viable_targets:
        # Prefer enemy units that are currently in melee with our allies (to free them)
        # If none in melee, pick a random target
        ally_stuck_in_melee = set(
            friendly for friendly in active_player.units if friendly.is_alive() and 
            any(util.distance(friendly.position, ene.position) <= 1 for ene in opposing_player.units if ene.is_alive())
        )
        if ally_stuck_in_melee:
            # Find enemies engaged with these allies
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

    # Identify if there is a friendly unit stuck in melee, and if so, try to charge the enemy it's fighting
    ally_in_melee = [
        friendly for friendly in active_player.units if friendly.is_alive() and 
        friendly.melee_target is not None
    ]

    enemies_in_range = [e for e in opposing_player.units if e.is_alive() and util.distance(chosen_unit.position, e.position) <= 12]

    if not enemies_in_range:
        print("no enemies in range")
        return

    # If we have allies in melee, try to charge the enemy that traps them
    if ally_in_melee:
        # Find all enemies trapping allies
        enemies_trapping_allies = [
            e for e in enemies_in_range 
            if any(util.distance(e.position, f.position) <= 1 for f in ally_in_melee)
        ]
        if enemies_trapping_allies:
            # Charge the closest enemy that is trapping an ally
            enemy_target = min(enemies_trapping_allies, key=lambda e: util.distance(chosen_unit.position, e.position))
        else:
            enemy_target = min(enemies_in_range, key=lambda e: util.distance(chosen_unit.position, e.position))
    else:
        enemy_target = min(enemies_in_range, key=lambda e: util.distance(chosen_unit.position, e.position))

    dist = util.distance(chosen_unit.position, enemy_target.position)
    charge_roll = roll_2d6()

    # Overwatch check
    if 'Overwatch' in enemy_target.keywords and not enemy_target.has_activated:
        # Enemy gets a missile attack before movement
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
