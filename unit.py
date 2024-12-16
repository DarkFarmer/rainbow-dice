import random
from model import Model
from armor import ARMOR_SAVES
from dice import roll_dice


class Unit:
    # Class-level counter for generating unique IDs
    _id_counter = 1

    def __init__(self, name, num_models, wounds_per_model, armor, movement, ap_cost,
                 missile_attack_dice, melee_attack_dice, attack_range,
                 special_rules=None, keywords=None):
        """
        :param missile_attack_dice: A list of dice types for missile attacks, e.g. ['blue', 'blue', 'green'].
        :param melee_attack_dice: A list of dice types for melee attacks, e.g. ['purple', 'purple'].
        """
        self.name = name
        self.initial_num_models = num_models  # Store initial count for degrade calculations
        self.num_models = num_models
        self.wounds_per_model = wounds_per_model
        self.armor = armor
        self.movement = movement
        self.ap_cost = ap_cost
        # Ensure we store copies to avoid unintended modifications
        self.base_missile_attack_dice = missile_attack_dice.copy() if missile_attack_dice else []
        self.base_melee_attack_dice = melee_attack_dice.copy() if melee_attack_dice else []
        self.attack_range = attack_range
        self.id = Unit._generate_unique_id()
        self.special_rules = special_rules if special_rules else []
        self.keywords = keywords if keywords else []
        self.models = [Model(wounds_per_model) for _ in range(num_models)]
        self.position = None
        self.melee_target = None
        self.has_activated = False
        self.alive = True
        self.shields_remaining = self._get_keyword_value('Shields', default=0)

        self.pending_casualties = 0  # For Last Stand
        self.last_stand_active = 'Last Stand' in self.keywords
        self.degrade_amount = self._get_keyword_value('Degrade', default=0)
        self.commander_value = self._get_keyword_value('Commander', default=0)

    @classmethod
    def _generate_unique_id(cls):
        unique_id = cls._id_counter
        cls._id_counter += 1
        return unique_id

    def is_locked_in_melee(self):
        return self.melee_target

    def _get_keyword_value(self, keyword, default=None):
        # Extract a value if keyword has a numeric parameter, e.g. "Commander 2"
        for item in self.keywords:
            if item.startswith(keyword):
                parts = item.split()
                for p in parts[1:]:
                    if p.isdigit():
                        return int(p)
        return default

    def is_alive(self):
        # If Last Stand is active, and not yet activated this turn, treat pending casualties as not removed yet.
        return any(m.is_alive() for m in self.models) or (self.last_stand_active and self.pending_casualties > 0 and not self.has_activated)

    def get_armor_save(self, phase='melee', attacker=None):
        base_save = ARMOR_SAVES.get(self.armor, 6)
        # Camouflage: improves save in missile phase by 1 step (if not ignored by Sharpshooter)
        if phase == 'missile' and 'Camouflage' in self.keywords:
            if not (attacker and 'Sharpshooter' in attacker.keywords):
                base_save = base_save - 1  # Better by one step

        # Clamp save at best 2+
        base_save = max(2, base_save)
        return base_save

    def get_attack_dice(self, phase, charging=False):
        # Start with base dice for the given phase
        if phase == 'missile':
            dice_pool = self.base_missile_attack_dice.copy()
        else:
            dice_pool = self.base_melee_attack_dice.copy()

        # Adjust the dice pool for lost models
        models_lost = self.initial_num_models - self.num_models
        if models_lost > 0:
            # Remove the weakest dice first
            dice_pool = dice_pool[models_lost:]

        # Attack Augmentation [Die]: add one die per model
        for keyword in self.keywords:
            if keyword.startswith('Attack Augmentation'):
                parts = keyword.split()
                if len(parts) > 2:
                    aug_die = parts[2]
                    for _ in range(self.num_models):
                        dice_pool.append(aug_die)

        # Crushing Charge [Die]: If charging, add one die per model
        if charging:
            for keyword in self.keywords:
                if keyword.startswith('Crushing Charge'):
                    parts = keyword.split()
                    if len(parts) > 2:
                        charge_die = parts[2]
                        for _ in range(self.num_models):
                            dice_pool.append(charge_die)

        # Degrade N: If less than half wounds remain, remove N dice
        if self.degrade_amount > 0:
            total_starting_wounds = self.initial_num_models * self.wounds_per_model
            current_wounds = sum(m.current_wounds for m in self.models)
            if current_wounds < (total_starting_wounds / 2.0):
                # Remove N dice from the end
                for _ in range(self.degrade_amount):
                    if dice_pool:
                        dice_pool.pop()

        return dice_pool

    def roll_attack_dice(self, dice_pool, slayer=False):
        """
        Roll the dice pool. If slayer is True, re-roll dice that generate mortal wounds until they generate no more.
        """
        total_wounds = {'normal': 0, 'double': 0, 'mortal': 0}

        for dice_type in dice_pool:
            if slayer:
                # Keep rolling this die until it produces no mortal wound
                while True:
                    dice_result = roll_dice(dice_type)
                    # Add results
                    for k in total_wounds:
                        total_wounds[k] += dice_result.get(k, 0)
                    # If it did not produce a mortal wound this time, break
                    if dice_result.get('mortal', 0) == 0:
                        break
            else:
                dice_result = roll_dice(dice_type)
                for k in total_wounds:
                    total_wounds[k] += dice_result.get(k, 0)

        return total_wounds

    def attack(self, target_unit, phase, charging=False):
        # Determine if Withering Fire or Relentless applies
        armor_save_modifier = 0
        if 'Withering Fire' in self.keywords and phase == 'missile':
            armor_save_modifier += 1
        if 'Relentless' in self.keywords and phase == 'melee':
            armor_save_modifier += 1

        print(f"{self.name} ({self.num_models} models) is attacking {target_unit.name} in the {phase} phase.")
        if charging:
            print(f"{self.name} is charging into combat!")

        dice_pool = self.get_attack_dice(phase, charging=charging)
        print(f"{self.name} is rolling {len(dice_pool)} dice: {dice_pool}")

        total_wounds = self.roll_attack_dice(dice_pool, slayer='Slayer' in self.keywords)
        print(f"{self.name} inflicted the following wounds: {total_wounds}")

        target_unit.defend(total_wounds, armor_save_modifier, attacker=self, phase=phase)

    def defend(self, incoming_wounds, armor_save_modifier, attacker=None, phase='melee'):
        # Calculate armor save with modifications
        armor_save = self.get_armor_save(phase=phase, attacker=attacker)
        armor_save += armor_save_modifier
        armor_save = min(6, max(2, armor_save))

        can_save_mortal = 'Lucky' in self.keywords
        total_incoming = sum(incoming_wounds.values())

        print(f"{self.name} is defending against {total_incoming} incoming wounds: {incoming_wounds}")
        print(f"{self.name}'s armor save is {armor_save} (modifier: {armor_save_modifier}).")

        # Shields
        wounds_to_ignore = min(self.shields_remaining, total_incoming)
        self.shields_remaining -= wounds_to_ignore
        wounds_to_assign = total_incoming - wounds_to_ignore
        if wounds_to_ignore > 0:
            print(f"{self.name} absorbed {wounds_to_ignore} wounds with shields.")

        wound_queue = (
            ['mortal'] * incoming_wounds['mortal'] +
            ['double'] * incoming_wounds['double'] +
            ['normal'] * incoming_wounds['normal']
        )[:wounds_to_assign]

        # If Assassin: attacker chooses casualties. We simulate by removing from the last model first.
        reverse_removal = ('Assassin' in (attacker.keywords if attacker else []))

        # Collect all alive models
        model_indices = [i for i, m in enumerate(self.models) if m.is_alive()]
        if reverse_removal:
            model_indices = list(reversed(model_indices))

        casualties = 0

        for wound_type in wound_queue:
            if not model_indices:
                break
            target_index = model_indices[0]
            model = self.models[target_index]

            # Roll save (except if mortal and no Lucky)
            save_roll = random.randint(1, 6)
            is_mortal = (wound_type == 'mortal')
            save_successful = (save_roll >= armor_save) if (not is_mortal or can_save_mortal) else False

            if not save_successful:
                damage = 2 if wound_type == 'double' else 1
                model.take_wound(damage)
                if not model.is_alive():
                    casualties += 1
                    model_indices.pop(0)  # model dead
                    print(f"{self.name} lost a model to {wound_type} damage.")
            else:
                print(f"{self.name} saved against {wound_type} damage with a roll of {save_roll}.")

        print(f"{self.name} took {casualties} casualties this phase.")

        # Handle Last Stand: if unit has not activated and has Last Stand,
        # do not remove casualties now, just store them.
        if self.last_stand_active and not self.has_activated:
            self.pending_casualties += casualties
        else:
            # Apply casualties immediately if no Last Stand or after they've activated.
            self.apply_pending_casualties()

        self.check_casualties()
    def check_casualties(self):
        alive_models = sum(1 for model in self.models if model.is_alive())
        self.num_models = alive_models
        if alive_models == 0:
            self.alive = False
            print(f"{self.name} has been wiped out.")
        else:
            print(f"{self.name} has {self.num_models} models remaining.")

    def apply_pending_casualties(self):
        # Pending casualties represent models already killed but not removed due to Last Stand.
        # Once we apply them, we run check_casualties() which cleans up dead models.
        pass

    def calculate_total_wounds(self):
        total_possible_wounds = len(self.models) * self.wounds_per_model
        total_current_wounds = sum(model.current_wounds for model in self.models if model.current_wounds > 0)
        return total_possible_wounds - total_current_wounds

    def clone(self):
        return Unit(
            name=self.name,
            num_models=self.num_models,
            wounds_per_model=self.wounds_per_model,
            armor=self.armor,
            movement=self.movement,
            ap_cost=self.ap_cost,
            missile_attack_dice=self.base_missile_attack_dice.copy(),
            melee_attack_dice=self.base_melee_attack_dice.copy(),
            attack_range=self.attack_range,
            special_rules=self.special_rules.copy(),
            keywords=self.keywords.copy(),
        )

    def regenerate(self):
        # If unit does nothing else this activation, restore 1D6 destroyed models
        # Only possible if some models were destroyed
        destroyed_count = self.initial_num_models - self.num_models
        if destroyed_count > 0:
            amount = random.randint(1, 6)
            amount = min(amount, destroyed_count)
            print(f"{self.name} is regenerating {amount} models.")
            # Restore that many models at full wounds
            for _ in range(amount):
                self.models.append(Model(self.wounds_per_model))
            self.num_models += amount
            self.alive = True
