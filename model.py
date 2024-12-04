class Model:
    def __init__(self, max_wounds):
        self.max_wounds = max_wounds
        self.current_wounds = max_wounds

    def take_wound(self, damage):
        self.current_wounds -= damage

    def is_alive(self):
        return self.current_wounds > 0
