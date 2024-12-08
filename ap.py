def determine_ap_allocation(player_a, player_b):
    a_total = player_a.total_ap_on_table()
    b_total = player_b.total_ap_on_table()
    largest = max(a_total, b_total)
    # Each player gets half of largest, rounded up
    from math import ceil
    ap_for_both = ceil(largest / 2)
    # Ensure a player doesn't get fewer AP than their largest unit's cost
    # (From rules: A player cannot have fewer AP than their largest unit’s cost)
    a_min = max(u.ap_cost for u in player_a.units) if player_a.units else 0
    b_min = max(u.ap_cost for u in player_b.units) if player_b.units else 0

    ap_for_a = max(ap_for_both, a_min)
    ap_for_b = max(ap_for_both, b_min)

    return ap_for_a, ap_for_b
