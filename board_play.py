import pygame
import sys
from board_objects import Board
from load_board import get_random_pips_game, parse_pips_json
from pathlib import Path


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
        }
        
        # Generate colors for each region
        self.region_colors = self._generate_region_colors()
        
        # Clock for frame rate
        self.clock = pygame.time.Clock()
        
        print(f"Initialized visualizer for {board.rows}x{board.cols} board")
    
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
        """Draw diamond-shaped constraint labels for each region"""
        for region in self.board.regions:
            # Calculate center position of region
            if not region.cells:
                continue
            
            center_r = sum(r for r, c in region.cells) / len(region.cells)
            center_c = sum(c for r, c in region.cells) / len(region.cells)
            
            x = int(center_c * self.cell_size + self.cell_size / 2)
            y = int(center_r * self.cell_size + self.cell_size / 2)
            
            # Get constraint text
            text = self._format_constraint(region)
            
            # Draw diamond shape
            size = 40
            points = [
                (x, y - size),      # top
                (x + size, y),      # right
                (x, y + size),      # bottom
                (x - size, y),      # left
            ]
            
            # Draw diamond with region color
            pygame.draw.polygon(self.screen, self.region_colors[region], points)
            pygame.draw.polygon(self.screen, self.COLORS['black'], points, 3)
            
            # Draw text
            text_surface = self.font_medium.render(text, True, self.COLORS['black'])
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
    
    def _format_constraint(self, region):
        """Format constraint text for display"""
        if region.type == 'equals':
            return '='
        elif region.type == 'notequals':
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
        """Draw dominoes at the bottom of the screen"""
        y_start = self.board.rows * self.cell_size + 20
        domino_width = 100
        domino_height = 50
        spacing = 20
        
        # Calculate starting x to center dominoes
        total_width = len(self.board.dominoes) * (domino_width + spacing) - spacing
        x_start = (self.width - total_width) // 2
        
        for i, domino in enumerate(self.board.dominoes):
            x = x_start + i * (domino_width + spacing)
            y = y_start
            
            # Draw domino rectangle
            rect = pygame.Rect(x, y, domino_width, domino_height)
            pygame.draw.rect(self.screen, self.COLORS['white'], rect)
            pygame.draw.rect(self.screen, self.COLORS['black'], rect, 3, border_radius=5)
            
            # Draw dividing line
            mid_x = x + domino_width // 2
            pygame.draw.line(
                self.screen,
                self.COLORS['black'],
                (mid_x, y),
                (mid_x, y + domino_height),
                2
            )
            
            # Draw dots for first value
            self._draw_domino_dots(
                x + domino_width // 4,
                y + domino_height // 2,
                domino.values[0],
                15
            )
            
            # Draw dots for second value
            self._draw_domino_dots(
                x + 3 * domino_width // 4,
                y + domino_height // 2,
                domino.values[1],
                15
            )
    
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
    
    def run(self):
        """Main loop to display the board"""
        print("\nDisplay Controls:")
        print("  ESC or close window - Exit")
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
            
            # Draw everything
            self.draw_board()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        print("Window closed")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple PIPS Board Visualizer')
    parser.add_argument('--file', type=str, help='Path to puzzle JSON file')
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], 
                       default='easy', help='Puzzle difficulty')
    parser.add_argument('--cell-size', type=int, default=100, 
                       help='Cell size in pixels')
    
    args = parser.parse_args()
    
    # Load board
    print("Loading puzzle...")
    if args.file:
        board = parse_pips_json(Path(args.file), difficulty=args.difficulty)
        print(f"Loaded: {args.file} ({args.difficulty})")
    else:
        board = get_random_pips_game()
    
    print(f"Board: {board.rows}x{board.cols}")
    print(f"Dominoes: {len(board.dominoes)}")
    print(f"Regions: {len(board.regions)}")
    
    # Create and run visualizer
    viz = SimpleBoardVisualizer(board, cell_size=args.cell_size)
    viz.run()


if __name__ == '__main__':
    main()