class ControlPoint:
    def __init__(self, x, y, id):
        self.x = x
        self.y = y
        self.id = id

class Battlefield:
    def __init__(self, width, height, control_points, terrain_map):
        self.width = width
        self.height = height
        self.control_points = control_points
        self.terrain_map = terrain_map
        # terrain_map could be a dict or matrix indicating what type of terrain is at each (x,y)
    def get_control_points(self):
        return self.control_points