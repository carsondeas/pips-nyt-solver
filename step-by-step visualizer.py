from pathlib import Path
from load_board import parse_pips_json
from csp import solve_pips  # Use the actual working solver!
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import copy


class PipsVisualizer:
    def __init__(self, board):
        self.board = board
        self.region_colors = self._generate_region_colors()

    def _generate_region_colors(self):
        colors = [
            '#FFB6C1', '#87CEEB', '#98FB98', '#DDA0DD', '#F0E68C',
            '#FFA07A', '#B0C4DE', '#FFDAB9', '#E0BBE4', '#FFE4B5',
            '#C1FFC1', '#FFD1DC', '#B4E7CE', '#FCE883', '#D4A5A5'
        ]

        region_map = {}
        for i, region in enumerate(self.board.regions):
            region_map[id(region)] = colors[i % len(colors)]

        return region_map

    def visualize(self, solution=None, title="Pips Puzzle", ax_board=None, ax_tray=None, domino_states=None):
        """Draw the board plus (optionally) the domino tray."""
        ax = ax_board if ax_board is not None else plt.gca()
        ax.clear()

        R, C = self.board.rows, self.board.cols

        for region in self.board.regions:
            color = self.region_colors[id(region)]

            for (r, c) in region.cells:
                rect = patches.Rectangle(
                    (c, R - r - 1), 1, 1,
                    linewidth=2,
                    edgecolor='black',
                    facecolor=color,
                    alpha=0.6
                )
                ax.add_patch(rect)

                if solution and (r, c) in solution:
                    value = solution[(r, c)]
                    ax.text(
                        c + 0.5, R - r - 0.5,
                        str(value),
                        ha='center', va='center',
                        fontsize=20, fontweight='bold'
                    )

        for region in self.board.regions:
            if region.cells:
                r, c = region.cells[0]

                if region.type == "equals":
                    label = "="
                elif region.type == "notequals":
                    label = "!="
                elif region.type == "sum":
                    label = f"sum={region.target}"
                elif region.type == "less":
                    label = f"<{region.target}"
                elif region.type == "greater":
                    label = f">{region.target}"
                else:
                    label = ""

                if label:
                    ax.text(
                        c + 0.15, R - r - 0.15,
                        label,
                        ha='left', va='top',
                        fontsize=12,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
                    )

        if solution:
            self._draw_domino_boundaries(ax, solution, R, C)

        ax.set_xlim(0, C)
        ax.set_ylim(0, R)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=16, fontweight='bold')
        if ax_tray is not None:
            self._draw_domino_tray(ax_tray, domino_states or {})

    def _draw_domino_boundaries(self, ax, solution, R, C):
        domino_pairs = {}

        for (r, c), val in solution.items():
            if (r, c + 1) in solution and (r, c) not in domino_pairs:
                domino_pairs[(r, c)] = (r, c + 1)
            elif (r + 1, c) in solution and (r, c) not in domino_pairs:
                domino_pairs[(r, c)] = (r + 1, c)

        for (r1, c1), (r2, c2) in domino_pairs.items():
            if r1 == r2:
                rect = patches.Rectangle(
                    (c1, R - r1 - 1), 2, 1,
                    linewidth=4,
                    edgecolor='darkblue',
                    facecolor='none'
                )
                ax.add_patch(rect)
            else:
                rect = patches.Rectangle(
                    (c1, R - r2 - 1), 1, 2,
                    linewidth=4,
                    edgecolor='darkblue',
                    facecolor='none'
                )
                ax.add_patch(rect)

    def _draw_domino_tray(self, ax, domino_states):
        """Render the full domino set along the bottom."""
        ax.clear()

        cols = 7
        domino_width = 2.0
        domino_height = 1.2
        spacing = 0.4

        status_colors = {
            "unplaced": "#d9d9d9",
            "active": "#ffd166",
            "placed": "#a3c4f3",
        }

        for idx, domino in enumerate(self.board.dominoes):
            row = idx // cols
            col = idx % cols

            x = col * (domino_width + spacing)
            y = row * (domino_height + spacing)

            state = domino_states.get(domino.id, "unplaced")
            color = status_colors.get(state, "#d9d9d9")

            rect = patches.Rectangle(
                (x, y),
                domino_width,
                domino_height,
                linewidth=2,
                edgecolor='black',
                facecolor=color
            )
            ax.add_patch(rect)

            ax.plot(
                [x + domino_width / 2, x + domino_width / 2],
                [y, y + domino_height],
                color="black",
                linewidth=2
            )

            a, b = domino.values
            ax.text(x + 0.5, y + domino_height / 2, str(a), ha="center", va="center", fontsize=12, fontweight="bold", zorder=3)
            ax.text(x + 1.5, y + domino_height / 2, str(b), ha="center", va="center", fontsize=12, fontweight="bold", zorder=3)

        total_rows = (len(self.board.dominoes) + cols - 1) // cols
        width = cols * (domino_width + spacing) - spacing
        height = total_rows * (domino_height + spacing) - spacing

        ax.set_xlim(-spacing, width + spacing)
        ax.set_ylim(-spacing, height + spacing)
        ax.invert_yaxis()
        ax.axis("off")
        ax.set_title("Domino Tray", fontsize=12, fontweight="bold")


def solve_and_collect_steps(board):
    """
    Solve puzzle using actual CSP solver, then reconstruct steps
    by solving again while recording each placement
    """
    # First, get the correct solution
    print("Solving puzzle...")
    result = solve_pips(board)

    # Handle both old and new return formats
    if isinstance(result, tuple):
        final_solution, stats = result
        print(f"  Nodes explored: {stats.get('nodes_explored', 'N/A')}")
    else:
        final_solution = result
        stats = None

    if not final_solution:
        print("No solution found!")
        return None, [], {}

    print(f"Solution found with {len(final_solution)} cells")

    # Now simulate the solving process step-by-step
    # by progressively revealing the solution
    steps = []
    steps.append(('start', {}, None))

    # Group cells into dominoes
    domino_placements = []
    processed = set()

    for (r, c), val in sorted(final_solution.items()):
        if (r, c) in processed:
            continue

        # Find the other half of this domino
        other_half = None
        if (r, c + 1) in final_solution and (r, c + 1) not in processed:
            other_half = (r, c + 1)
        elif (r + 1, c) in final_solution and (r + 1, c) not in processed:
            other_half = (r + 1, c)

        if other_half:
            domino_placements.append([(r, c), other_half])
            processed.add((r, c))
            processed.add(other_half)

    # Match placements to actual domino ids by value multiset
    placement_records = []
    domino_mapping = {}
    used_ids = set()

    value_to_ids = {}
    for domino in board.dominoes:
        key = tuple(sorted(domino.values))
        value_to_ids.setdefault(key, []).append(domino.id)

    for ids in value_to_ids.values():
        ids.sort()

    for cells in domino_placements:
        vals = tuple(sorted((final_solution[cells[0]], final_solution[cells[1]])))
        id_pool = value_to_ids.get(vals, [])

        if id_pool:
            match_id = id_pool.pop(0)
        else:
            remaining = [d.id for d in board.dominoes if d.id not in used_ids]
            match_id = min(remaining) if remaining else -1

        used_ids.add(match_id)
        placement_records.append((match_id, cells))
        domino_mapping[match_id] = cells

    # Create steps for each domino placement
    current_grid = {}
    for domino_id, cells in placement_records:
        steps.append(('selecting', copy.deepcopy(current_grid), domino_id))

        # Place domino
        for cell in cells:
            current_grid[cell] = final_solution[cell]

        steps.append(('place', copy.deepcopy(current_grid), domino_id))

    steps.append(('solved', copy.deepcopy(final_solution), None))

    return final_solution, steps, domino_mapping


def interactive_demo(use_random=True, date="2025-11-20", difficulty="easy", board=None):
    """Run interactive step-by-step display"""

    if board is None and use_random:
        from load_board import get_random_pips_game
        print("\nLoading random puzzle...")
        board = get_random_pips_game()
    elif board is None:
        print(f"\nLoading puzzle: {date} ({difficulty})")
        board = parse_pips_json(Path(f"all_boards/{date}.json"), difficulty)
    else:
        print("\nUsing provided board")

    print(f"Board size: {board.rows}x{board.cols}")
    print(f"Dominoes: {len(board.dominoes)}")
    print(f"Regions: {len(board.regions)}")

    input("\nPress Enter to solve...")

    # Solve and collect steps
    final_solution, steps, domino_mapping = solve_and_collect_steps(board)

    if not final_solution:
        return

    print(f"\nCollected {len(steps)} steps")
    input("Press Enter to start stepping through solution...")

    # Setup visualization
    viz = PipsVisualizer(board)
    plt.ion()
    fig = plt.figure(figsize=(10, 12))
    gs = fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.35)
    ax_board = fig.add_subplot(gs[0])
    ax_tray = fig.add_subplot(gs[1])

    print("\n" + "=" * 40)
    print("INTERACTIVE PIPS SOLVER")
    print("=" * 40 + "\n")

    step_num = 0
    skip_to_end = False

    for action, grid, domino_id in steps:
        if skip_to_end and action != 'solved':
            continue

        step_num += 1

        # Create title
        if action == 'start':
            title = f"Step {step_num}: Starting puzzle"
        elif action == 'selecting':
            title = f"Step {step_num}: Selecting domino {domino_id}"
        elif action == 'place':
            title = f"Step {step_num}: Placed domino {domino_id}"
        elif action == 'solved':
            title = f"Step {step_num}: SOLVED!"
        else:
            title = f"Step {step_num}: {action}"

        domino_states = {}
        for domino in board.dominoes:
            cells = domino_mapping.get(domino.id)
            if cells and all(cell in grid for cell in cells):
                domino_states[domino.id] = "placed"
            else:
                domino_states[domino.id] = "unplaced"

        if action == 'selecting' and domino_id is not None:
            domino_states[domino_id] = "active"

        # Display
        viz.visualize(
            grid,
            title=title,
            ax_board=ax_board,
            ax_tray=ax_tray,
            domino_states=domino_states
        )
        plt.draw()
        plt.pause(0.01)

        # Print info
        print("=" * 60)
        print(title)
        print("=" * 60)
        print(f"Cells filled: {len(grid)}")

        if action == 'solved':
            print("\nPUZZLE SOLVED!")
            print(f"Total cells: {len(grid)}")
            print(f"Expected cells: {sum(len(r.cells) for r in board.regions)}")

            # Verify completeness
            total_expected = sum(len(r.cells) for r in board.regions)
            if len(grid) == total_expected:
                print("All cells filled correctly!")
            else:
                print(f"Warning: Only {len(grid)}/{total_expected} cells filled")

        # Wait for user
        print("-" * 60)
        if action != 'solved':
            response = input("Press Enter (or 'q' to quit, 's' to skip to end): ")
            print()

            if response.lower() == 'q':
                print("Quitting...")
                plt.close()
                return
            elif response.lower() == 's':
                skip_to_end = True
                print("Skipping to solution...\n")

    print("\n" + "=" * 40)
    print("SUCCESS!")
    print("=" * 40)
    input("\nPress Enter to close...")
    plt.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Specific puzzle mode
        date = sys.argv[1]
        difficulty = sys.argv[2] if len(sys.argv) > 2 else "easy"
        interactive_demo(use_random=False, date=date, difficulty=difficulty)
    else:
        # Random puzzle mode (default)
        interactive_demo(use_random=True)
