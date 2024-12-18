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

    def apply_terrain_effects(self, battlefield, phase='missile'):
        """
        Check if this unit is in any terrain and apply the effects:
        - Forest: Add Camouflage and limit attack_range to 8" for missile attacks.
        - Building: Add Shields 1 on ranged attacks.
        - Hard Cover: Add Lucky keyword.
        
        This will return a set of temporary keywords and possibly adjust attack range.
        """
        if self.position is None:
            return set(), self.attack_range

        x, y = self.position
        temp_keywords = set()
        adjusted_range = self.attack_range

        for terrain in battlefield.terrain_map:
            # Check if unit is inside this terrain piece
            if (x >= terrain["x"] and x < terrain["x"] + terrain["width"] and
                y >= terrain["y"] and y < terrain["y"] + terrain["height"]):
                # Inside this terrain
                if terrain["type"] == "Forest":
                    temp_keywords.add("Camouflage")
                    if phase == 'missile':
                        adjusted_range = min(adjusted_range, 8)
                elif terrain["type"] == "Building":
                    # Shields 1 on ranged attacks
                    if phase == 'missile':
                        temp_keywords.add("Shields 1")
                elif terrain["type"] == "Hard Cover":
                    temp_keywords.add("Lucky")

        return temp_keywords, adjusted_range

    def get_armor_save(self, phase='melee', attacker=None, battlefield=None):
        # If battlefield provided, apply terrain effects
        terrain_keywords = set()
        if battlefield:
            terrain_keywords, _ = self.apply_terrain_effects(battlefield, phase=phase)

        # Combine terrain keywords with unit's keywords for the calculation
        effective_keywords = set(self.keywords).union(terrain_keywords)

        base_save = ARMOR_SAVES.get(self.armor, 6)
        # Camouflage check
        if phase == 'missile' and 'Camouflage' in effective_keywords:
            if not (attacker and 'Sharpshooter' in attacker.keywords):
                base_save = base_save - 1
        # Clamp save
        base_save = max(2, base_save)

        return base_save, effective_keywords

    def attack(self, target_unit, phase, charging=False, battlefield=None):
        # Determine Withering/Relentless after terrain
        save_mod = 0

        # Apply terrain to get effective keywords for attacking unit
        # Attack range also might change due to Forest
        terrain_keywords, adjusted_range = self.apply_terrain_effects(battlefield, phase=phase)
        effective_keywords = set(self.keywords).union(terrain_keywords)

        # Check range if phase is missile
        if phase == 'missile':
            # If distance > adjusted_range, no attack. (Assuming you have distance checks)
            # For simplicity, we ignore actual distance checks here.
            pass

        if 'Withering Fire' in effective_keywords and phase == 'missile':
            save_mod += 1
        if 'Relentless' in effective_keywords and phase == 'melee':
            save_mod += 1

        dice_pool = self.get_attack_dice(phase, charging=charging)
        total_wounds = self.roll_attack_dice(dice_pool, slayer='Slayer' in effective_keywords)

        # Let target defend, passing battlefield so target can also apply terrain effects
        target_unit.defend(total_wounds, save_mod, attacker=self, phase=phase, battlefield=battlefield)

    def defend(self, incoming_wounds, armor_save_modifier, attacker=None, phase='melee', battlefield=None):
        # Get armor save after terrain
        armor_save, effective_keywords = self.get_armor_save(phase=phase, attacker=attacker, battlefield=battlefield)
        armor_save += armor_save_modifier
        armor_save = min(6, max(2, armor_save))

        can_save_mortal = 'Lucky' in effective_keywords
        total_incoming = sum(incoming_wounds.values())

        # Check if Shields in effective keywords for ranged attacks
        if phase == 'missile':
            # Find any "Shields N" keyword
            shield_value = 0
            for kw in effective_keywords:
                if kw.startswith('Shields'):
                    parts = kw.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        shield_value = int(parts[1])
                        break
        else:
            shield_value = 0

        wounds_to_ignore = min(shield_value, total_incoming)
        self.shields_remaining -= wounds_to_ignore
        wounds_to_assign = total_incoming - wounds_to_ignore

        wound_queue = (
            ['mortal'] * incoming_wounds['mortal'] +
            ['double'] * incoming_wounds['double'] +
            ['normal'] * incoming_wounds['normal']
        )[:wounds_to_assign]

        reverse_removal = ('Assassin' in attacker.keywords if attacker else False)

        model_indices = [i for i, m in enumerate(self.models) if m.is_alive()]
        if reverse_removal:
            model_indices = list(reversed(model_indices))

        casualties = 0

        for wound_type in wound_queue:
            if not model_indices:
                break
            target_index = model_indices[0]
            model = self.models[target_index]

            save_roll = random.randint(1, 6)
            is_mortal = (wound_type == 'mortal')
            save_successful = (save_roll >= armor_save) if (not is_mortal or can_save_mortal) else False

            if not save_successful:
                damage = 2 if wound_type == 'double' else 1
                model.take_wound(damage)
                if not model.is_alive():
                    casualties += 1
                    model_indices.pop(0)

        if self.last_stand_active and not self.has_activated:
            self.pending_casualties += casualties
        else:
            self.apply_pending_casualties()

        self.check_casualties()

    def check_casualties(self):
        alive_models = sum(1 for model in self.models if model.is_alive())
        self.num_models = alive_models
        if alive_models == 0:
            self.alive = False
            #print(f"{self.name} has been wiped out.")
        #else:
            #print(f"{self.name} has {self.num_models} models remaining.")

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
            #print(f"{self.name} is regenerating {amount} models.")
            # Restore that many models at full wounds
            for _ in range(amount):
                self.models.append(Model(self.wounds_per_model))
            self.num_models += amount
            self.alive = True
