import heapq
from typing import Dict, List, Tuple

from board_objects import Board
from csp import region_ok_partial, region_ok_full

Grid = Dict[Tuple[int, int], int]
Placement = Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]


def build_region_lookup(board: Board) -> Dict[Tuple[int, int], object]:
    """Map each cell to its owning region for O(1) checks."""
    mapping: Dict[Tuple[int, int], object] = {}
    for region in board.regions:
        for cell in region.cells:
            mapping[cell] = region
    return mapping


def placement_is_valid(
    placement: Placement,
    grid: Grid,
    region_lookup: Dict[Tuple[int, int], object],
    valid_cells: set,
) -> bool:
    (c1, c2, vals) = placement
    v1, v2 = vals

    # both halves must be on valid puzzle cells and currently unused
    if c1 not in valid_cells or c2 not in valid_cells:
        return False
    if c1 in grid or c2 in grid:
        return False

    reg1 = region_lookup.get(c1)
    if reg1:
        vals1 = [grid[c] for c in reg1.cells if c in grid]
        vals1.append(v1)
        if reg1 is region_lookup.get(c2):
            vals1.append(v2)
        if not region_ok_partial(reg1, vals1):
            return False

    reg2 = region_lookup.get(c2)
    if reg2 and reg2 is not reg1:
        vals2 = [grid[c] for c in reg2.cells if c in grid]
        vals2.append(v2)
        if not region_ok_partial(reg2, vals2):
            return False

    return True


def heuristic(unfilled_cells: int) -> int:
    """Admissible lower bound: each domino covers two cells."""
    return (unfilled_cells + 1) // 2


def select_domino(
    used_mask: int,
    placements_per_domino: List[List[Placement]],
    grid: Grid,
    region_lookup: Dict[Tuple[int, int], object],
    valid_cells: set,
) -> Tuple[int, List[Placement]]:
    """Pick the first unplaced domino (no MRV heuristic)."""
    used_cells = set(grid.keys())

    for idx, placements in enumerate(placements_per_domino):
        if used_mask & (1 << idx):
            continue

        valid_domain = []
        for p in placements:
            (c1, c2, _) = p
            if c1 in used_cells or c2 in used_cells:
                continue
            if placement_is_valid(p, grid, region_lookup, valid_cells):
                valid_domain.append(p)

        return idx, valid_domain

    return -1, []


def is_goal(grid: Grid, board: Board, region_lookup: Dict[Tuple[int, int], object]) -> bool:
    if len(grid) != len(board.valid_cells):
        return False
    # ensure all regions are satisfied fully
    for region in board.regions:
        vals = [grid[c] for c in region.cells]
        if not region_ok_full(region, vals):
            return False
    return True


def solve_pips(board: Board):
    """A* search over partial domino placements."""
    placements_per_domino = [board.generate_domino_placements(d) for d in board.dominoes]
    region_lookup = build_region_lookup(board)
    valid_cells = board.valid_cells

    # state: (used_mask, grid)
    start_mask = 0
    start_grid: Grid = {}
    start_h = heuristic(len(valid_cells))

    # discoverd by not explored states
    frontier = []
    
    counter = 0
    # (f, g, counter, used_mask, grid, path)
    heapq.heappush(frontier, (start_h, 0, counter, start_mask, start_grid, []))

    visited = set()

    while frontier:
        f, g, _, used_mask, grid, path = heapq.heappop(frontier)

        state_key = (used_mask, tuple(sorted(grid.items())))
        if state_key in visited:
            continue
        visited.add(state_key)

        if is_goal(grid, board, region_lookup):
            return grid

        dom_idx, domain = select_domino(
            used_mask, placements_per_domino, grid, region_lookup, valid_cells
        )

        if dom_idx == -1 or not domain:
            continue

        for placement in domain:
            new_grid = dict(grid)
            (c1, c2, vals) = placement
            v1, v2 = vals
            new_grid[c1] = v1
            new_grid[c2] = v2

            new_mask = used_mask | (1 << dom_idx)
            unfilled = len(valid_cells) - len(new_grid)
            h = heuristic(unfilled)
            new_g = g + 1
            new_f = new_g + h
            counter += 1
            heapq.heappush(
                frontier,
                (new_f, new_g, counter, new_mask, new_grid, path + [(dom_idx, placement)]),
            )

    return None
