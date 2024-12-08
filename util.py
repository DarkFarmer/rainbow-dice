def distance(pos1, pos2):
    return abs(pos1[0]-pos2[0]) + abs(pos1[1]-pos2[1])

def count_models_in_range(player, cp, radius):
    count = 0
    for u in player.units:
        if u.is_alive() and distance(u.position, (cp.x, cp.y)) <= radius:
            count += u.num_models
    return count