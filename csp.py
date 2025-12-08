from functools import lru_cache
from collections import Counter

# check for partial placements
def region_ok_partial(region, values, unused_values):
    t = region.type
    target = region.target
    total_cells = len(region.cells)
    used_cells = len(values)
    remaining = total_cells - used_cells

    if t == "empty":
        return True

    if t == "equals":
        # determine target value
        if len(values) > 1 and len(set(values)) > 1:
            return False

        if len(values) == 0:
            return True 

        val = values[0]

        # check if there are enough remaining unused values
        if unused_values[val] < remaining:
            return False

        return True

    if t == "notequals":
        # used values must be unique
        if len(values) != len(set(values)):
            return False

        # check if enough distinct unused values exist
        used_set = set(values)
        distinct_available = 0
        for v, count in unused_values.items():
            if count > 0 and v not in used_set:
                distinct_available += 1

        if distinct_available < remaining:
            return False

        return True

    
    # Compute best-case min & max sums using unused values
    all_unused = []
    for val, cnt in unused_values.items():
        all_unused.extend([val] * cnt)

    # If not enough values left globally to fill the region, fail
    if len(all_unused) < remaining:
        return False

    # smallest possible fill:
    min_fill = sum(sorted(all_unused)[:remaining])
    # largest possible fill
    max_fill = sum(sorted(all_unused, reverse=True)[:remaining])
    current_sum = sum(values)
    min_possible = current_sum + min_fill
    max_possible = current_sum + max_fill

    if t == "less":
        return min_possible < target

    if t == "greater":
        return max_possible > target

    if t == "sum":
        return min_possible <= target and max_possible >= target

    return True

# similar to region_ok_partial but for full placements
def region_ok_full(region, values):
    t = region.type
    target = region.target

    if t == "empty":
        return True

    if t == "equals":
        return len(set(values)) == 1

    if t == "notequals":
        return len(values) == len(set(values))

    total = sum(values)

    if t == "less":
        return total < target

    if t == "greater":
        return total > target

    if t == "sum":
        return total == target

    return True


def solve_pips(board, return_stats=False):
    dominoes = board.dominoes
    regions = board.regions
    region_map = board.region_map

    # only cells that belong to the puzzle are valid; the bounding box may include holes
    valid_cells = set(region_map.keys())

    all_placements = board.generate_all_domino_placements()

    # create direct lookup of each region's cells 
    region_cells = {}
    for region in regions:
        for cell in region.cells:
            region_cells[cell] = region

    # track unassigned placements
    remaining_domains = [list(p) for p in all_placements]

    grid = {} 
    used = [False] * len(dominoes)
    solution = None

    stats = None
    if return_stats:
        stats = {
            "nodes": 0,
            "placements_tried": 0,
            "backtracks": 0,
            "pruned": 0,
            "constraint_checks": 0,
            "max_depth": 0,
        }
    unused_values = Counter()
    for d in dominoes:
        a, b = d.values
        unused_values[a] += 1
        unused_values[b] += 1


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
        if stats is not None:
            stats["constraint_checks"] += 1

        # both halves must be on valid puzzle cells
        if c1 not in valid_cells or c2 not in valid_cells:
            return False

        # cell 1 check
        reg1 = region_cells.get(c1)
        if reg1:
            vals = [grid[c] for c in reg1.cells if c in grid]
            vals.append(v1)
            # if both halves share the same region, include the second value
            if reg1 is region_cells.get(c2):
                vals.append(v2)
            if not region_ok_partial(reg1, vals, unused_values):
                return False

        # cell 2 check
        reg2 = region_cells.get(c2)
        if reg2 and reg2 is not reg1:
            vals = [grid[c] for c in reg2.cells if c in grid]
            vals.append(v2)
            if not region_ok_partial(reg2, vals, unused_values):
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
                if stats is not None:
                    stats["pruned"] += len(removed_i)
                removed.append((i, removed_i))
                remaining_domains[i] = new_domain

        return removed


    def undo_forward_check(removed):
        for idx, items in removed:
            remaining_domains[idx].extend(items)


    def dfs(depth=0, valid_cells=valid_cells):
        nonlocal solution

        if stats is not None:
            stats["nodes"] += 1
            stats["max_depth"] = max(stats["max_depth"], depth)

        if all(used):
            # ensure complete coverage and all regions satisfied
            if len(grid) != len(valid_cells) or set(grid.keys()) != valid_cells:
                return False
            for region in regions:
                vals = [grid[c] for c in region.cells]
                if not region_ok_full(region, vals):
                    return False
            solution = dict(grid)
            return True

        d = select_domino()
        used[d] = True

        placements = remaining_domains[d]

        for (c1, c2, vals) in placements:
            if stats is not None:
                stats["placements_tried"] += 1

            if c1 in grid or c2 in grid:
                continue

            v1, v2 = vals

            if not placement_is_valid(c1, c2, v1, v2):
                continue

            # place the domino
            grid[c1] = v1
            grid[c2] = v2

            unused_values[v1] -= 1
            unused_values[v2] -= 1

            # forward checking
            removed = forward_check(d)
            if removed is not None:
                # continue deeper
                if dfs(depth + 1):
                    return True
                # undo forward checking
                undo_forward_check(removed)
            
            unused_values[v1] += 1
            unused_values[v2] += 1

            # undo placement
            del grid[c1]
            del grid[c2]

        used[d] = False
        if stats is not None:
            stats["backtracks"] += 1
        return False



    # start dfs
    solved = dfs()
    if stats is not None:
        # placements_tried represents our step count for reporting
        stats["steps"] = stats.get("placements_tried", 0)
    if return_stats:
        return (solution if solved else None, stats)
    return solution if solved else None
