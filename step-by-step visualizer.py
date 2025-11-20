from pathlib import Path

import viz

from load_board import parse_pips_json
from visualizations import PipsVisualizer
from csp import region_ok_partial
import matplotlib.pyplot as plt

def solve_pips_interactive(board):
    R, C = board.rows, board.cols
    dominoes = board.dominoes
    regions = board.regions
    region_map = board.region_map

    def generate_domino_placements(domino):
        a, b = domino.values
        placements = []
        is_double = (a==b)

        for r in range(R):
            for c in range(C):
                if c+ 1 < C:
                    placements.append(((r, c), (r, c+1), (a, b)))
                    if not is_double:
                        placements.append(((r,c), (r,c+1), (b,a)))
                if r+1 < R:
                    placements.append(((r,c), (r+1,c), (a,b)))
                    if not is_double:
                        placements.append(((r,c), (r+1,c), (b,a)))

        return placements

    all_placements = [generate_domino_placements(d) for d in dominoes]
    region_cells = {cell: region for region in regions for cell in region.cells}
    remaining_domains = [list(p) for p in all_placements]

    grid = {}
    used = [False] * len(dominoes)
    step_count = [0]

    vis = PipsVisualizer(board)

    plt.ion()
    fig, ax = plt.subplots(figsize = (10,10))

    def show_step(action, domino_id = None):
        step_count[0] += 1

        ax.clear()
        plt.sca(ax)

        if action == 'start':
            title = f"Step {step_count[0]}: Starting puzzle"
        elif action == 'selecting':
            title = f"Step {step_count[0]}: Selecting next domino"
        elif action == 'place':
            domino = dominoes[domino_id]
            title = f"Step {step_count[0]}: Placeing next domino {domino_id} (values: {domino.values})"
        elif action == 'backtrack':
            title = f"Step {step_count[0]}: Backtracking puzzle, removing domino {domino_id})"
        elif action == 'solve':
            title = f"Step {step_count[0]}: Solved puzzle"
        else:
            title = f"Step {step_count[0]}: {action}"

        vis.visualize(grid.copy(), title=title)
        plt.draw()
        plt.pause(0.01)

        print ("\n" + "="*60)
        print(title)
        print("="*60)

        if action == 'start':
            print(f"Total dominoes to place: {len(dominoes)}")
            print(f"Board size: {R}x{C}")
            print(f"Regions: {len(regions)}")

        elif action == 'selecting':
            remaining = sum(1 for u in used if not u)
            print(f"Dominoes remaining: {remaining}/{len(dominoes)}")
            print(f"Cells filled: {len(grid)}")

        elif action == 'place':
            domino = dominoes[domino_id]
            print(f"Domino values: {domino.values}")
            print(f"Cells filled: {len(grid)}")
            print(f"Dominoes placed: {sum(used)}/{len(dominoes)}")

            # Show which cells were just filled
            for (r, c), val in grid.items():
                if (r, c) not in [k for k in list(grid.keys())[:-2]]:
                    reg = region_cells.get((r, c))
                    if reg:
                        print(f"  Cell ({r},{c}) = {val} [Region: {reg.type}]")

        elif action == 'backtrack':
            print(f"Removed domino {domino_id}")
            print(f"Cells filled: {len(grid)}")
            print("Trying different placement...")

        elif action == 'solved':
            print(f"\n Puzzle solved in {step_count[0]} steps!")
            print(f"Total cells filled: {len(grid)}")

            # Wait for user
        print("\n" + "-" * 60)
        response = input("Press Enter for next step (or 'q' to quit, 's' to skip to end): ")
        print()

        return response.lower()

    def select_domino():
        best = None
        best_size = 10 ** 18
        for i in range(len(dominoes)):
            if not used[i]:
                size = len(remaining_domains[i])
                if size < best_size:
                    best_size = size
                    best = i
        return best

    def placement_is_valid(c1, c2, v1, v2):
        reg1 = region_cells.get(c1)
        if reg1:
            vals = [grid[c] for c in reg1.cells if c in grid] + [v1]
            if not region_ok_partial(reg1, vals):
                return False
        reg2 = region_cells.get(c2)
        if reg2:
            vals = [grid[c] for c in reg2.cells if c in grid] + [v2]
            if not region_ok_partial(reg2, vals):
                return False
        return True

    def forward_check(dom_idx):
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

    skip_to_end = [False]

    def dfs():
        if all(used):
            if not skip_to_end[0]:
                show_step('solved')
            return True

        if not skip_to_end[0]:
            response = show_step('selecting')
            if response == 'q':
                print("Quitting...")
                plt.close()
                exit()
            elif response == 's':
                skip_to_end[0] = True
                print("Skipping to solution...")

        d = select_domino()
        used[d] = True
        placements = remaining_domains[d]

        for (c1, c2, vals) in placements:
            if c1 in grid or c2 in grid:
                continue

            v1, v2 = vals

            if not placement_is_valid(c1, c2, v1, v2):
                continue

            # Place domino
            grid[c1] = v1
            grid[c2] = v2

            if not skip_to_end[0]:
                response = show_step('place', d)
                if response == 'q':
                    print("Quitting...")
                    plt.close()
                    exit()
                elif response == 's':
                    skip_to_end[0] = True
                    print("Skipping to solution...")

            removed = forward_check(d)
            if removed is not None:
                if dfs():
                    return True
                undo_forward_check(removed)

            # Backtrack
            del grid[c1]
            del grid[c2]

            if not skip_to_end[0]:
                response = show_step('backtrack', d)
                if response == 'q':
                    print("Quitting...")
                    plt.close()
                    exit()
                elif response == 's':
                    skip_to_end[0] = True
                    print("Skipping to solution...")

        used[d] = False
        return False

     # Start solving
    show_step('start')

    success = dfs()

    if success:
        if skip_to_end[0]:
            # Show final solution if we skipped
            ax.clear()
            plt.sca(ax)
            viz.visualize(grid.copy(), title=f"✓ SOLVED in {step_count[0]} steps!")
            plt.draw()

        print("SUCCESS! Puzzle solved!")
        input("\nPress Enter to close...")
        plt.close()
        return grid
    else:
        print("\n No solution found")
        plt.close()
        return None

def interactive_demo(date="2025-11-20", difficulty="easy"):
    """
    Run interactive solver demo

    Args:
        date: Puzzle date (YYYY-MM-DD)
        difficulty: "easy", "medium", or "hard"
    """
    print(f"\nLoading puzzle: {date} ({difficulty})")
    board = parse_pips_json(Path(f"all_boards/{date}.json"), difficulty)

    print(f"Board size: {board.rows}x{board.cols}")
    print(f"Dominoes: {len(board.dominoes)}")
    print(f"Regions: {len(board.regions)}")

    input("\nPress Enter to start solving...")

    solution = solve_pips_interactive(board)

    return solution

if __name__ == "__main__":
    import sys

    # Command line arguments
    date = sys.argv[1] if len(sys.argv) > 1 else "2025-11-20"
    difficulty = sys.argv[2] if len(sys.argv) > 2 else "easy"

    interactive_demo(date, difficulty)

