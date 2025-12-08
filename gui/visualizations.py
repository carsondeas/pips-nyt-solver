from pathlib import Path
import sys

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import to_rgba
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from load_board import parse_pips_json  # noqa: E402


class PipsVisualizer:
    def __init__(self, board):
        self.board = board
        self.region_colors = self._generate_region_colors()

    def _generate_region_colors(self):
        """Assign distinct colors to each region"""
        colors = [
            '#FFB6C1', '#87CEEB', '#98FB98', '#DDA0DD', '#F0E68C',
            '#FFA07A', '#B0C4DE', '#FFDAB9', '#E0BBE4', '#FFE4B5',
            '#C1FFC1', '#FFD1DC', '#B4E7CE', '#FCE883', '#D4A5A5'
        ]

        region_map = {}
        for i, region in enumerate(self.board.regions):
            region_map[id(region)] = colors[i % len(colors)]

        return region_map

    def visualize(self, solution=None, title="Pips Puzzle", show_values=True):
        """
        Visualize the board with optional solution

        Args:
            solution: dict mapping (r,c) -> pip_value (from solver)
            title: plot title
            show_values: whether to display pip numbers
        """
        fig, ax = plt.subplots(figsize=(10, 10))

        R, C = self.board.rows, self.board.cols

        # Draw each cell
        for region in self.board.regions:
            color = self.region_colors[id(region)]

            for (r, c) in region.cells:
                # Draw cell background
                rect = patches.Rectangle(
                    (c, R - r - 1), 1, 1,
                    linewidth=2,
                    edgecolor='black',
                    facecolor=color,
                    alpha=0.6
                )
                ax.add_patch(rect)

                # Show pip value if solution provided
                if solution and (r, c) in solution:
                    value = solution[(r, c)]
                    ax.text(
                        c + 0.5, R - r - 0.5,
                        str(value),
                        ha='center', va='center',
                        fontsize=20, fontweight='bold'
                    )

        # Draw region constraint labels
        for region in self.board.regions:
            if region.cells:
                # Place label at first cell of region
                r, c = region.cells[0]

                # Create constraint text
                if region.type == "equals":
                    label = "="
                elif region.type == "notequals":
                    label = "≠"
                elif region.type == "sum":
                    label = f"Σ={region.target}"
                elif region.type == "less":
                    label = f"<{region.target}"
                elif region.type == "greater":
                    label = f">{region.target}"
                else:  # empty
                    label = ""

                if label:
                    # Draw label in top-left corner of region
                    ax.text(
                        c + 0.15, R - r - 0.15,
                        label,
                        ha='left', va='top',
                        fontsize=12,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
                    )

        # Draw domino boundaries if solution exists
        if solution:
            self._draw_domino_boundaries(ax, solution, R, C)

        # Set axis properties
        ax.set_xlim(0, C)
        ax.set_ylim(0, R)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=16, fontweight='bold')

        plt.tight_layout()
        return fig, ax

    def _draw_domino_boundaries(self, ax, solution, R, C):
        """Draw thick lines between domino halves"""
        # Track which cells belong to same domino
        domino_pairs = {}

        # Find domino pairs by checking adjacent cells
        for (r, c), val in solution.items():
            # Check right neighbor
            if (r, c + 1) in solution and (r, c) not in domino_pairs:
                # These form a horizontal domino
                domino_pairs[(r, c)] = (r, c + 1)
            # Check bottom neighbor
            elif (r + 1, c) in solution and (r, c) not in domino_pairs:
                # These form a vertical domino
                domino_pairs[(r, c)] = (r + 1, c)

        # Draw thick borders around each domino
        for (r1, c1), (r2, c2) in domino_pairs.items():
            if r1 == r2:  # Horizontal domino
                # Draw thick border around both cells
                rect = patches.Rectangle(
                    (c1, R - r1 - 1), 2, 1,
                    linewidth=4,
                    edgecolor='darkblue',
                    facecolor='none'
                )
                ax.add_patch(rect)
            else:  # Vertical domino
                rect = patches.Rectangle(
                    (c1, R - r2 - 1), 1, 2,
                    linewidth=4,
                    edgecolor='darkblue',
                    facecolor='none'
                )
                ax.add_patch(rect)

    def save(self, filename, solution=None, title="Pips Puzzle"):
        """Save visualization to file"""
        fig, ax = self.visualize(solution, title)
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved visualization to {filename}")

    def show(self, solution=None, title="Pips Puzzle"):
        """Display visualization"""
        self.visualize(solution, title)
        plt.show()


def visualize_comparison(board, csp_solution, sa_solution):
    """Show CSP and SA solutions side-by-side"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    viz = PipsVisualizer(board)

    # Draw CSP solution
    plt.sca(ax1)
    viz.visualize(csp_solution, title="CSP Solution")

    # Draw SA solution
    plt.sca(ax2)
    viz.visualize(sa_solution, title="Simulated Annealing Solution")

    plt.tight_layout()
    plt.show()


# Example usage functions
def test_visualization():
    """Test the visualizer on a random puzzle"""
    from load_board import get_random_pips_game
    from csp import solve_pips

    board = get_random_pips_game()
    viz = PipsVisualizer(board)
    viz.show(title="Empty Puzzle")

    print("Solving with CSP...")
    result = solve_pips(board)  # Changed: single return value

    # Handle both old and new return formats
    if isinstance(result, tuple):
        solution, stats = result
    else:
        solution = result
        stats = None

    if solution:
        print("Visualizing solution...")
        viz.show(solution, title="Solved Puzzle")
        viz.save("solved_puzzle.png", solution)
    else:
        print("No solution found!")



if __name__ == "__main__":
    test_visualization()
