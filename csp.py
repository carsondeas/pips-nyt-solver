from functools import lru_cache

# check for partial placements
def region_ok_partial(region, values):
    t = region.type
    target = region.target

    if t == "empty":
        return True

    if t == "equals":
        # all values must be the same
        return len(set(values)) <= 1

    if t == "notequals":
        # all values must differ
        return len(values) == len(set(values))

    if t == "less":
        return all(v < target for v in values)

    if t == "greater":
        return all(v > target for v in values)

    if t == "sum":
        # partial sums fine as long as we dont exceed target
        return sum(values) <= target

    return True


def solve_pips(board):
    R, C = board.rows, board.cols
    dominoes = board.dominoes
    regions = board.regions
    region_map = board.region_map

    # generate all domino placements
    def generate_domino_placements(domino):
        a, b = domino.values
        placements = []

        for r in range(R):
            for c in range(C):

                # horizontal
                if c + 1 < C:
                    placements.append(((r, c), (r, c+1), (a, b)))
                    placements.append(((r, c), (r, c+1), (b, a)))

                # vertical
                if r + 1 < R:
                    placements.append(((r, c), (r+1, c), (a, b)))
                    placements.append(((r, c), (r+1, c), (b, a)))

        return placements

    all_placements = [
        generate_domino_placements(d) for d in dominoes
    ]


    # create direct lookup of each region's cells 
    region_cells = {}
    for region in regions:
        for cell in region.cells:
            region_cells[cell] = region

    # track unassigned placements
    remaining_domains = [list(p) for p in all_placements]

    grid = {} 
    used = [False] * len(dominoes)


    # choose next domino with fewest remaining placements
    def select_domino():
        best = None
        best_size = 10**18
        for i in range(len(dominoes)):
            if not used[i]:
                size = len(remaining_domains[i])
                if size < best_size:
                    best_size = size
                    best = i
        return best


    # attempt placement and check validity
    def placement_is_valid(c1, c2, v1, v2):
        # cell 1 check
        reg1 = region_cells.get(c1)
        if reg1:
            vals = [grid[c] for c in reg1.cells if c in grid] + [v1]
            if not region_ok_partial(reg1, vals):
                return False

        # cell 2 check
        reg2 = region_cells.get(c2)
        if reg2:
            vals = [grid[c] for c in reg2.cells if c in grid] + [v2]
            if not region_ok_partial(reg2, vals):
                return False

        return True


    # after placing a domino, eliminate placements that now overlap occupied cells or violate regions
    def forward_check(dom_idx):

        # list of (index, [placements_removed])
        removed = [] 
        used_cells = set(grid.keys())

        for i in range(len(dominoes)):
            if used[i]:
                continue

            new_domain = []
            removed_i = []
            for placement in remaining_domains[i]:
                (c1, c2, vals) = placement
                if c1 in used_cells or c2 in used_cells:
                    removed_i.append(placement)
                    continue

                v1, v2 = vals
                if not placement_is_valid(c1, c2, v1, v2):
                    removed_i.append(placement)
                    continue

                new_domain.append(placement)

            if removed_i:
                removed.append((i, removed_i))
                remaining_domains[i] = new_domain

        return removed


    def undo_forward_check(removed):
        for idx, items in removed:
            remaining_domains[idx].extend(items)


    def dfs():
        if all(used):
            return True

        d = select_domino()
        used[d] = True

        placements = remaining_domains[d]

        for (c1, c2, vals) in placements:
            if c1 in grid or c2 in grid:
                continue

            v1, v2 = vals

            if not placement_is_valid(c1, c2, v1, v2):
                continue

            # place the domino
            grid[c1] = v1
            grid[c2] = v2

            # forward checking
            removed = forward_check(d)
            if removed is not None:
                # continue deeper
                if dfs():
                    return True
                # undo forward checking
                undo_forward_check(removed)

            # undo placement
            del grid[c1]
            del grid[c2]

        used[d] = False
        return False



    # start dfs
    if dfs():
        return grid
    return None
