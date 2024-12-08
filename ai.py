import util
def ai_choose_unit_to_activate(player, remaining_ap):
    # Must activate highest AP unit first if they choose to use it at all
    # So we find the highest AP cost unit that we can afford.
    units_by_ap = player.get_units_by_ap()
    for unit in units_by_ap:
        if unit.ap_cost <= remaining_ap:
            return unit
    return None

def ai_move_unit_towards_control_point(unit, battlefield):
    # Simple logic: find nearest control point and move closer
    nearest_cp = min(battlefield.control_points,
                     key=lambda cp: util.distance(unit.position, (cp.x, cp.y)))
    # Move unit closer by up to unit.movement inches (1 inch per grid cell for simplicity)
    unit.position = move_closer(unit.position, (nearest_cp.x, nearest_cp.y), unit.movement)

def move_closer(start, end, steps):
    # Simple approach: move along x until aligned, then along y
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    move_x = min(steps, abs(dx))
    steps -= move_x
    new_x = x1 + move_x * (1 if dx > 0 else -1)

    move_y = min(steps, abs(dy))
    new_y = y1 + move_y * (1 if dy > 0 else -1)
    return (new_x, new_y)

def find_enemy_in_range(unit, enemies):
    # Check if any enemy is in shooting range (for simplicity, say range=10)
    # In your actual code, you'd use the unit's ranged weapons range.
    for enemy in enemies:
        if enemy.is_alive():
            if util.distance(unit.position, enemy.position) <= 10:
                return enemy
    return None