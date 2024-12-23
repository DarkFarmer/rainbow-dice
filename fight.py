import random

def melee_favorable(attacker, defender):
    """
    Placeholder for melee favorability logic.
    Eventually, this might be replaced with a more complex, possibly ML-driven decision.
    For now, let's just return True.
    """
    return True

import random

def melee_favorable(attacker, defender):
    """
    Placeholder for melee favorability logic.
    Eventually, this might be replaced with a more complex, possibly ML-driven decision.
    For now, let's just return True.
    """
    return True

def simulate_fight(unit_a, unit_b, active_player, battlefield, initial_distance=24, phase='missile', charging=False):
    """
    Simulates a fight between two units, tracking kills and updating active player's stats.
    Prints combat updates for better insight.
    :param unit_a: The attacking unit.
    :param unit_b: The defending unit.
    :param battlefield: The battlefield object containing terrain info.
    :param initial_distance: Starting distance between the units.
    :param active_player: The player controlling the attacking unit.
    :param phase: The phase of the fight ('missile' or 'melee').
    :param charging: Boolean indicating if unit_a is charging (for melee).
    """
    print(f"\nCombat begins! {unit_a.name} vs {unit_b.name}")
    print(f"Phase: {'Melee' if phase == 'melee' else 'Missile'} | Charging: {charging}")
    print(f"{unit_a.name} starting models: {unit_a.num_models}, {unit_b.name} starting models: {unit_b.num_models}")

    # Initial conditions
    distance = initial_distance

    # Track wounds inflicted by phase
    total_wounds_by_phase = {
        unit_a.name: {'missile': 0, 'melee': 0},
        unit_b.name: {'missile': 0, 'melee': 0},
    }

    # Perform a single ranged attack if possible
    if phase == 'missile':
        initial_models = unit_b.num_models
        print(f"{unit_a.name} launches a missile attack!")
        unit_a.attack(unit_b, 'missile', charging=False, battlefield=battlefield)
        wounds_inflicted = unit_b.calculate_total_wounds()
        total_wounds_by_phase[unit_a.name]['missile'] += wounds_inflicted

        # Count kills from missile attack
        models_killed = initial_models - unit_b.num_models
        if models_killed > 0:
            print(f"{unit_a.name} killed {models_killed} models in the missile phase!")
        else:
            print(f"{unit_a.name}'s missile attack had no effect.")

        if active_player:
            active_player.missile_kills += models_killed

        # Check if defending unit died from missile attack
        if not unit_b.is_alive():
            print(f"{unit_b.name} has been wiped out by missile fire!")
            return {
                "winner": unit_a.name,
                "survivors": unit_a.num_models,
                "turns": 1,
                "wounds_by_phase": total_wounds_by_phase,
            }

    # Perform a melee attack if in melee phase
    if phase == 'melee':
        if charging:
            print(f"{unit_a.name} charges into melee with {unit_b.name}!")
            unit_a.add_melee_engagement(unit_b)
            unit_b.add_melee_engagement(unit_a)

        initial_models = unit_b.num_models
        print(f"{unit_a.name} attacks {unit_b.name} in melee!")
        unit_a.attack(unit_b, 'melee', charging=charging, battlefield=battlefield)
        wounds_inflicted = unit_b.calculate_total_wounds()
        total_wounds_by_phase[unit_a.name]['melee'] += wounds_inflicted

        # Count kills from melee attack
        models_killed = initial_models - unit_b.num_models
        if models_killed > 0:
            print(f"{unit_a.name} killed {models_killed} models in melee!")
        else:
            print(f"{unit_a.name}'s melee attack had no effect.")

        if active_player:
            active_player.melee_kills += models_killed

        # Check if defending unit died from melee attack
        if not unit_b.is_alive():
            print(f"{unit_b.name} has been wiped out in melee!")
            unit_a.remove_melee_engagement(unit_b)
            unit_b.remove_melee_engagement(unit_a)
            return {
                "winner": unit_a.name,
                "survivors": unit_a.num_models,
                "turns": 1,
                "wounds_by_phase": total_wounds_by_phase,
            }

    # If we get here, both units are still alive after one sequence of attacks.
    print(f"Combat continues! {unit_a.name} and {unit_b.name} are still fighting.")
    return {
        "winner": None,
        "survivors": None,
        "turns": 1,
        "wounds_by_phase": total_wounds_by_phase,
    }

