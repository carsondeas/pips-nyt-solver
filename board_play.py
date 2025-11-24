import pygame
import sys
from typing import Dict, List, Optional, Tuple
import time
from board_objects import Board
from csp import solve_pips as solve_csp
from simulated_annealing import solve_pips as solve_anneal


class SimpleBoardVisualizer:
    """Simple visualizer to display PIPS board"""
    
    def __init__(self, board, cell_size=100):
        """
        Initialize the visualizer
        
        Args:
            board: Board object containing dominoes and regions
            cell_size: Size of each cell in pixels
        """
        pygame.init()
        
        self.board = board
        self.cell_size = cell_size
        
        # Calculate required width for dominoes at bottom
        domino_width = 100
        spacing = 20
        dominoes_total_width = len(board.dominoes) * (domino_width + spacing) + spacing
        
        # Calculate window size - use max of board width and dominoes width
        board_width = board.cols * cell_size
        self.width = max(board_width, dominoes_total_width)
        self.height = board.rows * cell_size + 200  # Extra space for dominoes at bottom
        
        # Create window
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("PIPS Puzzle Board")
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Colors - pastel palette
        self.COLORS = {
            'white': (255, 255, 255),
            'black': (30, 30, 30),
            'grid': (200, 200, 200),
            'label_bg': (100, 100, 100),
            'highlight': (30, 144, 255),
            'placed': (46, 139, 87),
        }
        
        # Generate colors for each region
        self.region_colors = self._generate_region_colors()
        
        # Clock for frame rate
        self.clock = pygame.time.Clock()

        # Step-by-step state
        self.steps: List[Tuple[str, Dict[Tuple[int, int], int], Optional[Tuple[Tuple[int, int], Tuple[int, int]]], Optional[int]]] = []
        self.step_index: int = 0
        self.current_grid: Dict[Tuple[int, int], int] = {}
        self.current_action: str = 'start'
        self.current_highlight: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
        self.current_domino_id: Optional[int] = None
        self.placed_domino_ids = set()
        self.autoplay: bool = False
        self.autoplay_delay_s: float = 0.5
        self._last_advance_time: float = time.time()
        
        print(f"Initialized visualizer for {board.rows}x{board.cols} board")

    def set_steps(self, steps, autoplay=False, delay_s=0.5):
        """Attach step sequence produced by a solver"""
        self.steps = steps or []
        self.autoplay = autoplay
        self.autoplay_delay_s = max(0.05, float(delay_s))
        self.step_index = 0
        if self.steps:
            self._apply_step(0)
    
    def _generate_region_colors(self):
        """Generate soft colors for each region"""
        colors = {}
        palette = [
            (255, 220, 225),  # light pink
            (220, 235, 255),  # light blue
            (255, 245, 220),  # light yellow
            (230, 255, 230),  # light green
            (240, 230, 255),  # light purple
            (255, 240, 225),  # light orange
            (230, 245, 255),  # pale cyan
            (255, 230, 240),  # pale rose
            (235, 255, 245),  # mint
            (250, 240, 230),  # cream
        ]
        
        for i, region in enumerate(self.board.regions):
            colors[region] = palette[i % len(palette)]
        
        return colors
    
    def draw_board(self):
        """Draw the complete board"""
        # Fill background
        self.screen.fill(self.COLORS['white'])
        
        # Draw regions
        self._draw_regions()
        
        # Draw grid lines
        self._draw_grid()
        
        # Draw region labels (constraint badges)
        self._draw_constraint_labels()

        # Draw any filled values
        self._draw_grid_values()

        # Highlight current step placement
        self._draw_current_highlight()
        
        # Draw dominoes at bottom
        self._draw_dominoes()
    
    def _draw_regions(self):
        """Draw colored regions"""
        for region in self.board.regions:
            color = self.region_colors[region]
            
            # Draw each cell in the region
            for (r, c) in region.cells:
                x = c * self.cell_size
                y = r * self.cell_size
                
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, color, rect)
                
                # Draw dashed border for region
                pygame.draw.rect(self.screen, (150, 150, 150), rect, 2, border_radius=5)
    
    def _draw_grid(self):
        """Draw grid lines"""
        # Vertical lines
        for c in range(self.board.cols + 1):
            x = c * self.cell_size
            pygame.draw.line(
                self.screen,
                self.COLORS['grid'],
                (x, 0),
                (x, self.board.rows * self.cell_size),
                1
            )
        
        # Horizontal lines
        for r in range(self.board.rows + 1):
            y = r * self.cell_size
            pygame.draw.line(
                self.screen,
                self.COLORS['grid'],
                (0, y),
                (self.board.cols * self.cell_size, y),
                1
            )
    
    def _draw_constraint_labels(self):
        """Draw compact rule badges at the top-left corner of each region"""
        padding = 6
        for region in self.board.regions:
            if not region.cells:
                continue

            # Anchor to the actual top-left-most cell in this region
            top_r, top_c = min(region.cells, key=lambda rc: (rc[0], rc[1]))
            x = top_c * self.cell_size + padding
            y = top_r * self.cell_size + padding

            text = self._format_constraint(region)
            if not text:
                continue

            text_surface = self.font_small.render(text, True, self.COLORS['black'])
            text_rect = text_surface.get_rect(topleft=(x, y))

            bg_rect = text_rect.inflate(8, 4)
            pygame.draw.rect(self.screen, self.COLORS['white'], bg_rect, 0, border_radius=6)
            pygame.draw.rect(self.screen, self.COLORS['black'], bg_rect, 1, border_radius=6)

            self.screen.blit(text_surface, text_rect)
    
    def _format_constraint(self, region):
        """Format constraint text for display"""
        if region.type == 'equals':
            return '='
        elif region.type in ('unequal', 'notequals'):
            return '≠'
        elif region.type == 'sum':
            return str(region.target)
        elif region.type == 'less':
            return f'<{region.target}'
        elif region.type == 'greater':
            return f'>{region.target}'
        elif region.type == 'empty':
            return ''
        return '?'
    
    def _draw_dominoes(self):
        """Draw remaining (unplaced) dominoes at the bottom using numbers"""
        y_start = self.board.rows * self.cell_size + 20
        domino_width = 90
        domino_height = 52
        spacing = 16

        remaining = [d for d in self.board.dominoes if d.id not in self.placed_domino_ids]
        if not remaining:
            return

        total_width = len(remaining) * (domino_width + spacing) - spacing
        x_start = (self.width - total_width) // 2

        for i, domino in enumerate(remaining):
            x = x_start + i * (domino_width + spacing)
            y = y_start

            rect = pygame.Rect(x, y, domino_width, domino_height)
            pygame.draw.rect(self.screen, self.COLORS['white'], rect)
            pygame.draw.rect(self.screen, self.COLORS['black'], rect, 3, border_radius=5)

            mid_x = x + domino_width // 2
            pygame.draw.line(self.screen, self.COLORS['black'], (mid_x, y), (mid_x, y + domino_height), 2)

            left_val, right_val = domino.values
            left_text = self.font_medium.render(str(left_val), True, self.COLORS['black'])
            right_text = self.font_medium.render(str(right_val), True, self.COLORS['black'])
            left_rect = left_text.get_rect(center=(x + domino_width // 4, y + domino_height // 2))
            right_rect = right_text.get_rect(center=(x + 3 * domino_width // 4, y + domino_height // 2))
            self.screen.blit(left_text, left_rect)
            self.screen.blit(right_text, right_rect)
    
    def _draw_domino_dots(self, center_x, center_y, value, size):
        """Draw dots on domino to represent value (0-6)"""
        dot_radius = 4
        offset = size // 3
        
        # Dot positions for different values
        positions = {
            0: [],
            1: [(0, 0)],
            2: [(-offset, -offset), (offset, offset)],
            3: [(-offset, -offset), (0, 0), (offset, offset)],
            4: [(-offset, -offset), (offset, -offset), 
                (-offset, offset), (offset, offset)],
            5: [(-offset, -offset), (offset, -offset), (0, 0),
                (-offset, offset), (offset, offset)],
            6: [(-offset, -offset), (offset, -offset),
                (-offset, 0), (offset, 0),
                (-offset, offset), (offset, offset)],
        }
        
        if value in positions:
            for dx, dy in positions[value]:
                pygame.draw.circle(
                    self.screen,
                    self.COLORS['black'],
                    (center_x + dx, center_y + dy),
                    dot_radius
                )

    def _draw_grid_values(self):
        """Draw numbers for any filled cells in the current grid"""
        if not self.current_grid:
            return
        for (r, c), val in self.current_grid.items():
            x = int(c * self.cell_size + self.cell_size / 2)
            y = int(r * self.cell_size + self.cell_size / 2)
            text_surface = self.font_large.render(str(val), True, self.COLORS['black'])
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)

    def _draw_current_highlight(self):
        """Draw a border around the currently selected/placed domino"""
        if not self.current_highlight:
            return
        (r1, c1), (r2, c2) = self.current_highlight
        if r1 == r2:
            x = min(c1, c2) * self.cell_size
            y = r1 * self.cell_size
            w = 2 * self.cell_size
            h = self.cell_size
        else:
            x = c1 * self.cell_size
            y = min(r1, r2) * self.cell_size
            w = self.cell_size
            h = 2 * self.cell_size
        rect = pygame.Rect(x, y, w, h)
        color = self.COLORS['highlight'] if self.current_action == 'selecting' else self.COLORS['placed']
        pygame.draw.rect(self.screen, color, rect, 6, border_radius=8)
    
    def run(self):
        """Main loop to display the board"""
        print("\nDisplay Controls:")
        print("  ESC or close window - Exit")
        print("  SPACE/RIGHT - Next step")
        print("  LEFT - Previous step")
        print("  A - Toggle autoplay")
        print("  R - Reset to start")
        print("\nShowing board...\n")

        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                        self._advance_step(+1)
                    elif event.key == pygame.K_LEFT:
                        self._advance_step(-1)
                    elif event.key == pygame.K_a:
                        self.autoplay = not self.autoplay
                        self._last_advance_time = time.time()
                        print(f"Autoplay: {'ON' if self.autoplay else 'OFF'}")
                    elif event.key == pygame.K_r:
                        self._jump_to(0)

            # Autoplay step advance
            if self.autoplay and self.steps:
                now = time.time()
                if now - self._last_advance_time >= self.autoplay_delay_s:
                    self._last_advance_time = now
                    self._advance_step(+1)
            
            # Draw everything
            self.draw_board()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        print("Window closed")

    def _apply_step(self, idx: int):
        """Apply step at index to update current state"""
        if not self.steps:
            self.current_action = 'start'
            self.current_grid = {}
            self.current_highlight = None
            self.step_index = 0
            return
        idx = max(0, min(idx, len(self.steps) - 1))
        action, grid_snapshot, placement, domino_id = self.steps[idx]
        self.current_action = action
        self.current_grid = grid_snapshot
        self.current_highlight = placement
        self.current_domino_id = domino_id
        self.step_index = idx

        # recompute placed domino ids up to and including this step
        placed = set()
        for a, _g, _p, d_id in self.steps[:idx + 1]:
            if a == 'place' and d_id is not None:
                placed.add(d_id)
        self.placed_domino_ids = placed

    def _advance_step(self, delta: int):
        if not self.steps:
            return
        new_idx = self.step_index + delta
        new_idx = max(0, min(new_idx, len(self.steps) - 1))
        if new_idx != self.step_index:
            self._apply_step(new_idx)

    def _jump_to(self, idx: int):
        if not self.steps:
            return
        self._apply_step(idx)


def run_pygame_visualizer(
    board: Board,
    solver: str = "csp",
    cell_size: int = 100,
    auto: bool = False,
    delay: float = 0.5,
    debug: bool = False,
):
    """Solve a board and launch the pygame visualizer."""
    if board is None:
        raise ValueError("board must be provided")

    print(f"Board: {board.rows}x{board.cols}")
    print(f"Dominoes: {len(board.dominoes)}")
    print(f"Regions: {len(board.regions)}")
    print(f"Solving using: {solver.upper()}")

    if solver == "csp":
        solution = solve_csp(board)
    elif solver == "anneal":
        solution = solve_anneal(board)
    else:
        raise ValueError(f"Unknown solver: {solver}")

    if not solution:
        print("No solution found. Displaying board only.")
        steps = []
    else:
        if debug:
            print("\n=== Solver Solution (cell -> value) ===")
            for (r, c) in sorted(solution.keys()):
                print(f"({r},{c}) = {solution[(r,c)]}")
            print("=== End Solution ===\n")
            _debug_print_solution_grid(solution, board)
        steps = _build_steps_from_solution(solution, board, debug=debug)
        print(f"Built {len(steps)} steps.")

    viz = SimpleBoardVisualizer(board, cell_size=cell_size)
    if steps:
        viz.set_steps(steps, autoplay=auto, delay_s=delay)
    viz.run()


def _build_steps_from_solution(final_solution: Dict[Tuple[int, int], int], board: Board, debug: bool = False):
    """Create a list of (action, grid_snapshot, placement_cells, domino_id) steps from final grid.
    """
    steps: List[Tuple[str, Dict[Tuple[int, int], int], Optional[Tuple[Tuple[int, int], Tuple[int, int]]], Optional[int]]] = []
    steps.append(('start', {}, None, None))

    # Build availability map: unordered (a,b) -> list of domino ids
    def key_unordered(a: int, b: int) -> Tuple[int, int]:
        return (a, b) if a <= b else (b, a)

    available: Dict[Tuple[int, int], List[int]] = {}
    for d in board.dominoes:
        ka = key_unordered(d.values[0], d.values[1])
        available.setdefault(ka, []).append(d.id)

    # Process cells in order; choose a neighbor that matches an available domino
    processed = set()
    current_grid: Dict[Tuple[int, int], int] = {}

    for (r, c) in sorted(final_solution.keys()):
        if (r, c) in processed:
            continue

        v = final_solution[(r, c)]
        neighbors = [(r, c + 1), (r + 1, c), (r, c - 1), (r - 1, c)]

        chosen = None
        for nr, nc in neighbors:
            if (nr, nc) not in final_solution or (nr, nc) in processed:
                continue
            vn = final_solution[(nr, nc)]
            k = key_unordered(v, vn)
            ids = available.get(k, [])
            if ids:
                did = ids.pop(0)
                chosen = (((r, c), (nr, nc)), did)
                if debug:
                    dom_vals = next((d.values for d in board.dominoes if d.id == did), None)
                    print(f"[map] cells {(r, c)}<->({nr, nc}) values ({v}|{vn}) -> domino #{did} values {dom_vals}")
                break

        if not chosen:
            # No neighbor fits any available domino. Warn and skip pairing this cell.
            if debug:
                print(f"[warn] no available domino fits cell {(r, c)} value {v}; neighbors tried {neighbors}")
            processed.add((r, c))
            continue

        cells, domino_id = chosen

        # Step: selecting
        steps.append(('selecting', dict(current_grid), cells, domino_id))

        # Step: place values
        (r1, c1), (r2, c2) = cells
        current_grid[(r1, c1)] = final_solution[(r1, c1)]
        current_grid[(r2, c2)] = final_solution[(r2, c2)]
        steps.append(('place', dict(current_grid), cells, domino_id))

        # Mark both halves processed
        processed.add((r1, c1))
        processed.add((r2, c2))

    # done
    steps.append(('solved', dict(final_solution), None, None))
    return steps


def _debug_print_solution_grid(grid: Dict[Tuple[int, int], int], board: Board):
    """Pretty-print the solution as an RxC grid for quick visual verification."""
    print("Grid view (rows top->bottom, cols left->right):")
    for r in range(board.rows):
        row_vals = []
        for c in range(board.cols):
            if (r, c) in board.valid_cells if hasattr(board, 'valid_cells') else True:
                v = grid.get((r, c))
                row_vals.append('.' if v is None else str(v))
            else:
                row_vals.append(' ')
        print(' '.join(row_vals))
    print()

if __name__ == '__main__':
    print("This module is now launched via runner.py (use --pygame).")
