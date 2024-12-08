from unit import Unit
import game
from player import Player
import battlefield

def main():
    unit1 = Unit(
        name="Solar Knights",
        num_models=5,
        wounds_per_model=2,
        armor='Medium Armor',
        movement=6,
        ap_cost=4,
        missile_attack_dice=['Blue'] * 5,
        melee_attack_dice=['Green'] * 5,
        attack_range=18,
        special_rules=None,  # No special rules provided for this unit
        keywords=['Withering Fire']
    )

    unit2 = Unit(
        name="Alien Warriors",
        num_models=10,
        wounds_per_model=1,
        armor='Light Armor',
        movement=8,
        ap_cost=3,
        missile_attack_dice=[],  # No missile attack dice for this unit
        melee_attack_dice=['Pink'] * 10,
        attack_range=0,
        special_rules=None,  # No special rules provided for this unit
        keywords=['Relentless']
    )

    player1 = Player(
        name="Frank",
        units = [unit1, unit1]
    )
    
    player2 = Player(
        name="Dee",
        units = [unit2, unit2, unit2]
    )

    cp1 = battlefield.ControlPoint(3,5)
    cp2 = battlefield.ControlPoint(2,3)


    game.play_game(player1, player2, battlefield.Battlefield(6,4,[cp1, cp2],[]))

if __name__ == "__main__":
    main()
