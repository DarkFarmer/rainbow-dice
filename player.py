class Player:
    def __init__(self, name, units):
        self.name = name
        self.units = units
        self.score = 0
        self.melee_kills = 0
        self.missile_kills = 0
        self.remaining_ap = 0  # New attribute to track unused AP

    def total_ap_on_table(self):
        return sum(unit.ap_cost for unit in self.units if unit.is_alive())

    def get_units_by_ap(self):
        # Sort units by AP cost descending
        return sorted(
            [u for u in self.units if u.is_alive() and not u.has_activated],
            key=lambda x: x.ap_cost,
            reverse=True,
        )
