import random
from model import Model
from armor import ARMOR_SAVES
from dice import roll_dice


class Unit:
    # Class-level counter for generating unique IDs
    _id_counter = 1

    def __init__(self, name, num_models, wounds_per_model, armor, movement, ap_cost, missile_attack_dice, melee_attack_dice,
                 attack_range, special_rules=None, keywords=None):
        self.name = name
        self.num_models = num_models
        self.wounds_per_model = wounds_per_model
        self.armor = armor
        self.movement = movement
        self.ap_cost = ap_cost  # Action Point cost
        self.missile_attack_dice = missile_attack_dice
        self.melee_attack_dice = melee_attack_dice
        self.attack_range = attack_range  # Missile range in inches
        self.id = Unit._generate_unique_id()  # Assign unique ID
        self.special_rules = special_rules if special_rules else []
        self.keywords = keywords if keywords else []  # List of keywords
        self.models = [Model(wounds_per_model) for _ in range(num_models)]
        self.position = None  # (x, y) position on the battlefield
        self.in_melee = False
        self.has_activated = False
        self.locked_in_melee = False
        self.alive = True
        self.shields_remaining = self._get_keyword_value('Shields', default=0)

    @classmethod
    def _generate_unique_id(cls):
        unique_id = cls._id_counter
        cls._id_counter += 1
        return unique_id

    def is_locked_in_melee(self):
        return self.locked_in_melee
    def _get_keyword_value(self, keyword, default=None):
        for item in self.keywords:
            if item.startswith(keyword):
                parts = item.split()
                if len(parts) > 1 and parts[1].isdigit():
                    return int(parts[1])
        return default

    def is_alive(self):
        return any(model.is_alive() for model in self.models)

    def get_armor_save(self, phase='melee'):
        save = ARMOR_SAVES.get(self.armor, 6)
        if phase == 'missile' and 'Camouflage' in self.keywords:
            save += 1
        return max(2, min(save, 6))

    def attack(self, target_unit, phase):
        attack_dice = self.missile_attack_dice if phase == 'missile' else self.melee_attack_dice
        total_wounds = {'normal': 0, 'double': 0, 'mortal': 0}
        
        for dice_type in attack_dice:
            dice_result = roll_dice(dice_type)
            for key in total_wounds:
                total_wounds[key] += dice_result.get(key, 0)
        
        if 'Overwatch' in self.keywords and phase == 'melee':
            overwatch_wounds = {'normal': 0, 'double': 0, 'mortal': 0}
            for dice_type in self.missile_attack_dice:
                dice_result = roll_dice(dice_type)
                for key in overwatch_wounds:
                    overwatch_wounds[key] += dice_result.get(key, 0)
            target_unit.defend(overwatch_wounds, armor_save_modifier=0)

        target_unit.defend(total_wounds, armor_save_modifier=0)

    def defend(self, incoming_wounds, armor_save_modifier):
        
        armor_save = self.get_armor_save() + armor_save_modifier
        armor_save = max(2, min(armor_save, 6))
        
        can_save_mortal = 'Lucky' in self.keywords

        wounds_to_ignore = min(self.shields_remaining, sum(incoming_wounds.values()))
        self.shields_remaining -= wounds_to_ignore
        wounds_to_assign = sum(incoming_wounds.values()) - wounds_to_ignore

        wound_queue = (
            ['mortal'] * incoming_wounds['mortal'] +
            ['double'] * incoming_wounds['double'] +
            ['normal'] * incoming_wounds['normal']
        )[:wounds_to_assign]

        model_index = 0
        while wound_queue and model_index < len(self.models):
            model = self.models[model_index]
            if not model.is_alive():
                model_index += 1
                continue
            wound_type = wound_queue.pop(0)
            save_roll = random.randint(1, 6)
            save_successful = save_roll >= armor_save if wound_type != 'mortal' or can_save_mortal else False
            if not save_successful:
                damage = 1 if wound_type == 'normal' else 2
                model.take_wound(damage)
            if not model.is_alive():
                model_index += 1
        self.check_casualties()

    def check_casualties(self):
        alive_models = sum(1 for model in self.models if model.is_alive())
        self.num_models = alive_models
        if alive_models == 0:
            self.alive = False

    def calculate_total_wounds(self):
        total_possible_wounds = len(self.models) * self.wounds_per_model
        total_current_wounds = sum(model.current_wounds for model in self.models)
        return total_possible_wounds - total_current_wounds

    def clone(self):
        return Unit(
            name=self.name,
            num_models=self.num_models,
            wounds_per_model=self.wounds_per_model,
            armor=self.armor,
            movement=self.movement,
            ap_cost=self.ap_cost,
            missile_attack_dice=self.missile_attack_dice.copy(),
            melee_attack_dice=self.melee_attack_dice.copy(),
            attack_range=self.attack_range,
            special_rules=self.special_rules.copy(),
            keywords=self.keywords.copy(),
        )
