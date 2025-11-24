import random
import math


# generate all possible placements for each domino
def generate_all_placements(board):
    R, C = board.rows, board.cols
    placements_per_domino = []

    for domino in board.dominoes:
        a, b = domino.values
        options = []

        for r in range(R):
            for c in range(C):
                # horizontal
                if c + 1 < C:
                    options.append(((r, c), (r, c+1), (a, b)))
                    options.append(((r, c), (r, c+1), (b, a)))

                # vertical
                if r + 1 < R:
                    options.append(((r, c), (r+1, c), (a, b)))
                    options.append(((r, c), (r+1, c), (b, a)))

        placements_per_domino.append(options)

    return placements_per_domino


# get the penalty for the region
def region_energy(region, grid):

    vals = [grid[c] for c in region.cells if c in grid]

    if not vals:
        return 0

    t = region.type
    target = region.target

    if t == "empty":
        return 0

    if t == "equals":
        return 0 if len(set(vals)) == 1 else 1

    if t == "notequals":
        return 0 if len(vals) == len(set(vals)) else 1

    if t == "less":
        return sum(1 for v in vals if not (v < target))

    if t == "greater":
        return sum(1 for v in vals if not (v > target))

    if t == "sum":
        return abs(sum(vals) - target)

    return 0


# used to compute the penalty of a state
def compute_energy(state, board): 

    grid = {}
    overlap_penalty = 0

    # place all dominoes
    for (c1, c2, (v1, v2)) in state:
        # overlap detection
        if c1 in grid or c2 in grid:
            overlap_penalty += 10_000
        grid[c1] = v1
        grid[c2] = v2

    # region penalties
    region_penalty = 0
    for region in board.regions:
        region_penalty += region_energy(region, grid)

    return overlap_penalty * 10 + region_penalty


# generate a random initial state
def random_initial_state(placement_options):
    state = []
    for options in placement_options:
        state.append(random.choice(options))
    return state


# choose a random neighbor state
def random_neighbor(state, placement_options):
    new_state = list(state)

    # choose a domino to modify
    idx = random.randrange(len(new_state))

    # sometimes swap two dominoes
    if random.random() < 0.3:
        j = random.randrange(len(new_state))
        new_state[idx], new_state[j] = new_state[j], new_state[idx]
    else:
        # sometimes reassign its placement (small jump)
        new_state[idx] = random.choice(placement_options[idx])

    return new_state


# convert state into final grid mapping
def state_to_grid(state):
    grid = {}
    for (c1, c2, (v1, v2)) in state:
        grid[c1] = v1
        grid[c2] = v2
    return grid

def solve_pips(board,
               T_start=5.0,
               cooling=0.9995,
               max_iters=300000,
               restarts=12):

    placement_options = [
        board.generate_domino_placements(d) for d in board.dominoes
    ]

    best_global = None
    best_global_energy = float("inf")

    for restart in range(restarts):

        state = random_initial_state(placement_options)
        energy = compute_energy(state, board)

        T = T_start

        for it in range(max_iters):

            # if perfect solution
            if energy == 0:
                return state_to_grid(state)

            # neighbor
            neighbor = random_neighbor(state, placement_options)
            e2 = compute_energy(neighbor, board)

            # accept if better or sometimes if worse
            if e2 < energy:
                state, energy = neighbor, e2
            else:
                if random.random() < math.exp((energy - e2) / T):
                    state, energy = neighbor, e2

            T *= cooling

        # track best over all restarts
        if energy < best_global_energy:
            best_global_energy = energy
            best_global = state

    # only return if solved
    return state_to_grid(best_global) if best_global_energy == 0 else None
