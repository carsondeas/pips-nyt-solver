import pygame
import sys
from typing import Dict, List, Optional, Tuple
import time
from board_objects import Board
from csp import solve_pips as solve_csp
from simulated_annealing import solve_pips as solve_anneal

## Used AI to assist in coding this file.
class SimpleBoardVisualizer:
    
    def __init__(self, board, cell_size=100):
        pygame.init()
        
        self.board = board
        self.cell_size = cell_size
        
        domino_w = 100
        spacing = 20
        dom_total = len(board.dominoes) * (domino_w + spacing) + spacing
        bw = board.cols * cell_size
        self.width = max(bw, dom_total)
        self.height = board.rows * cell_size + 200
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("PIPS Puzzle Board")
        
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        self.COLORS = {
            'white': (255, 255, 255),
            'black': (30, 30, 30),
            'grid': (200, 200, 200),
            'label_bg': (100, 100, 100),
            'highlight': (30, 144, 255),
            'placed': (46, 139, 87),
        }
        
        self.region_colors = self._generate_region_colors()
        self.clock = pygame.time.Clock()

        self.steps = []
        self.step_index = 0
        self.current_grid = {}
        self.current_action = 'start'
        self.current_highlight = None
        self.current_domino_id = None
        self.placed_domino_ids = set()
        self.autoplay = False
        self.autoplay_delay_s = 0.5
        self._last_advance_time = time.time()
        
        print(f"Initialized visualizer for {board.rows}x{board.cols} board")

    def set_steps(self, steps, autoplay=False, delay_s=0.5):
        self.steps = steps or []
        self.autoplay = autoplay
        self.autoplay_delay_s = max(0.05, float(delay_s))
        self.step_index = 0
        if self.steps:
            self._apply_step(0)
    
    def _generate_region_colors(self):
        colors = {}
        palette = [
            (255, 220, 225), (220, 235, 255), (255, 245, 220),
            (230, 255, 230), (240, 230, 255), (255, 240, 225),
            (230, 245, 255), (255, 230, 240), (235, 255, 245),
            (250, 240, 230),
        ]
        
        for i, region in enumerate(self.board.regions):
            colors[region] = palette[i % len(palette)]
        
        return colors
    
    def draw_board(self):
        self.screen.fill(self.COLORS['white'])
        self._draw_regions()
        self._draw_grid()
        self._draw_constraint_labels()
        self._draw_grid_values()
        self._draw_current_highlight()
        self._draw_dominoes()
    
    def _draw_regions(self):
        for region in self.board.regions:
            color = self.region_colors[region]
            
            for (r, c) in region.cells:
                x = c * self.cell_size
                y = r * self.cell_size
                
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (150, 150, 150), rect, 2, border_radius=5)
    
    def _draw_grid(self):
        for c in range(self.board.cols + 1):
            x = c * self.cell_size
            pygame.draw.line(self.screen, self.COLORS['grid'], 
                           (x, 0), (x, self.board.rows * self.cell_size), 1)
        
        for r in range(self.board.rows + 1):
            y = r * self.cell_size
            pygame.draw.line(self.screen, self.COLORS['grid'],
                           (0, y), (self.board.cols * self.cell_size, y), 1)
    
    def _draw_constraint_labels(self):
        padding = 6
        for region in self.board.regions:
            if not region.cells:
                continue

            top_r, top_c = min(region.cells, key=lambda rc: (rc[0], rc[1]))
            x = top_c * self.cell_size + padding
            y = top_r * self.cell_size + padding

            text = self._format_constraint(region)
            if not text:
                continue

            txt_surf = self.font_small.render(text, True, self.COLORS['black'])
            txt_rect = txt_surf.get_rect(topleft=(x, y))

            bg = txt_rect.inflate(8, 4)
            pygame.draw.rect(self.screen, self.COLORS['white'], bg, 0, border_radius=6)
            pygame.draw.rect(self.screen, self.COLORS['black'], bg, 1, border_radius=6)

            self.screen.blit(txt_surf, txt_rect)
    
    def _format_constraint(self, region):
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
        y_start = self.board.rows * self.cell_size + 20
        dw = 90
        dh = 52
        gap = 16

        remaining = [d for d in self.board.dominoes if d.id not in self.placed_domino_ids]
        if not remaining:
            return

        total_w = len(remaining) * (dw + gap) - gap
        x_start = (self.width - total_w) // 2

        for i, dom in enumerate(remaining):
            x = x_start + i * (dw + gap)
            y = y_start

            rect = pygame.Rect(x, y, dw, dh)
            pygame.draw.rect(self.screen, self.COLORS['white'], rect)
            pygame.draw.rect(self.screen, self.COLORS['black'], rect, 3, border_radius=5)

            mid = x + dw // 2
            pygame.draw.line(self.screen, self.COLORS['black'], (mid, y), (mid, y + dh), 2)

            lval, rval = dom.values
            ltxt = self.font_medium.render(str(lval), True, self.COLORS['black'])
            rtxt = self.font_medium.render(str(rval), True, self.COLORS['black'])
            lrect = ltxt.get_rect(center=(x + dw // 4, y + dh // 2))
            rrect = rtxt.get_rect(center=(x + 3 * dw // 4, y + dh // 2))
            self.screen.blit(ltxt, lrect)
            self.screen.blit(rtxt, rrect)
    
    def _draw_domino_dots(self, cx, cy, val, size):
        r = 4
        off = size // 3
        
        dots = {
            0: [],
            1: [(0, 0)],
            2: [(-off, -off), (off, off)],
            3: [(-off, -off), (0, 0), (off, off)],
            4: [(-off, -off), (off, -off), (-off, off), (off, off)],
            5: [(-off, -off), (off, -off), (0, 0), (-off, off), (off, off)],
            6: [(-off, -off), (off, -off), (-off, 0), (off, 0), (-off, off), (off, off)],
        }
        
        if val in dots:
            for dx, dy in dots[val]:
                pygame.draw.circle(self.screen, self.COLORS['black'], 
                                 (cx + dx, cy + dy), r)

    def _draw_grid_values(self):
        if not self.current_grid:
            return
        for (r, c), val in self.current_grid.items():
            x = int(c * self.cell_size + self.cell_size / 2)
            y = int(r * self.cell_size + self.cell_size / 2)
            txt = self.font_large.render(str(val), True, self.COLORS['black'])
            rect = txt.get_rect(center=(x, y))
            self.screen.blit(txt, rect)

    def _draw_current_highlight(self):
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
        col = self.COLORS['highlight'] if self.current_action == 'selecting' else self.COLORS['placed']
        pygame.draw.rect(self.screen, col, rect, 6, border_radius=8)
    
    def run(self):
        print("\nControls: ESC=exit, SPACE/RIGHT=next, LEFT=prev, A=autoplay, R=reset\n")

        running = True
        while running:
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

            if self.autoplay and self.steps:
                now = time.time()
                if now - self._last_advance_time >= self.autoplay_delay_s:
                    self._last_advance_time = now
                    self._advance_step(+1)
            
            self.draw_board()
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

    def _apply_step(self, idx):
        if not self.steps:
            self.current_action = 'start'
            self.current_grid = {}
            self.current_highlight = None
            self.step_index = 0
            return
        idx = max(0, min(idx, len(self.steps) - 1))
        action, grid_snap, placement, dom_id = self.steps[idx]
        self.current_action = action
        self.current_grid = grid_snap
        self.current_highlight = placement
        self.current_domino_id = dom_id
        self.step_index = idx

        placed = set()
        for a, _g, _p, d_id in self.steps[:idx + 1]:
            if a == 'place' and d_id is not None:
                placed.add(d_id)
        self.placed_domino_ids = placed

    def _advance_step(self, delta):
        if not self.steps:
            return
        new_idx = self.step_index + delta
        new_idx = max(0, min(new_idx, len(self.steps) - 1))
        if new_idx != self.step_index:
            self._apply_step(new_idx)

    def _jump_to(self, idx):
        if not self.steps:
            return
        self._apply_step(idx)


def run_pygame_visualizer(board, solver="csp", cell_size=100, 
                          auto=False, delay=0.5, debug=False):
    if board is None:
        raise ValueError("board must be provided")

    print(f"Board: {board.rows}x{board.cols}")
    print(f"Dominoes: {len(board.dominoes)}")
    print(f"Regions: {len(board.regions)}")
    print(f"Solving with: {solver.upper()}")

    if solver == "csp":
        solution = solve_csp(board)
    elif solver == "anneal":
        solution = solve_anneal(board)
    else:
        raise ValueError(f"Unknown solver: {solver}")

    if not solution:
        print("No solution found - showing board only")
        steps = []
    else:
        if debug:
            for (r, c) in sorted(solution.keys()):
                print(f"({r},{c}) = {solution[(r,c)]}")
            _debug_print_grid(solution, board)
        steps = _build_steps(solution, board, debug=debug)
        print(f"Built {len(steps)} steps")

    viz = SimpleBoardVisualizer(board, cell_size=cell_size)
    if steps:
        viz.set_steps(steps, autoplay=auto, delay_s=delay)
    viz.run()


def _build_steps(final_sol, board, debug=False):
    steps = []
    steps.append(('start', {}, None, None))

    def norm_key(a, b):
        return (a, b) if a <= b else (b, a)

    avail = {}
    for d in board.dominoes:
        k = norm_key(d.values[0], d.values[1])
        avail.setdefault(k, []).append(d.id)

    processed = set()
    curr = {}

    for (r, c) in sorted(final_sol.keys()):
        if (r, c) in processed:
            continue

        v = final_sol[(r, c)]
        nbrs = [(r, c + 1), (r + 1, c), (r, c - 1), (r - 1, c)]

        chosen = None
        for nr, nc in nbrs:
            if (nr, nc) not in final_sol or (nr, nc) in processed:
                continue
            vn = final_sol[(nr, nc)]
            k = norm_key(v, vn)
            ids = avail.get(k, [])
            if ids:
                did = ids.pop(0)
                chosen = (((r, c), (nr, nc)), did)
                if debug:
                    dvals = next((d.values for d in board.dominoes if d.id == did), None)
                    print(f"map: {(r, c)}<->{(nr, nc)} vals ({v}|{vn}) -> dom #{did} {dvals}")
                break

        if not chosen:
            if debug:
                print(f"warn: no domino for cell {(r, c)} val {v}")
            processed.add((r, c))
            continue

        cells, dom_id = chosen

        steps.append(('selecting', dict(curr), cells, dom_id))

        (r1, c1), (r2, c2) = cells
        curr[(r1, c1)] = final_sol[(r1, c1)]
        curr[(r2, c2)] = final_sol[(r2, c2)]
        steps.append(('place', dict(curr), cells, dom_id))

        processed.add((r1, c1))
        processed.add((r2, c2))

    steps.append(('solved', dict(final_sol), None, None))
    return steps


def _debug_print_grid(grid, board):
    print("Grid view:")
    for r in range(board.rows):
        vals = []
        for c in range(board.cols):
            if (r, c) in board.valid_cells if hasattr(board, 'valid_cells') else True:
                v = grid.get((r, c))
                vals.append('.' if v is None else str(v))
            else:
                vals.append(' ')
        print(' '.join(vals))
    print()

if __name__ == '__main__':
    print("Launch via runner.py with --pygame flag")