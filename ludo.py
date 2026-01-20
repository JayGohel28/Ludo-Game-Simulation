import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
BOARD_SIZE = 15
SQUARE_SIZE = WIDTH // BOARD_SIZE
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

# Player colors
PLAYER_COLORS = [RED, GREEN, BLUE, YELLOW]

# Board positions (0-51 for main path, then private paths)
# Define the path coordinates
PATH_POSITIONS = []
for i in range(52):
    if i < 5:  # Bottom right to right
        x, y = 14, 14 - i
    elif i < 11:  # Right to top right
        x, y = 14 - (i - 5), 9
    elif i < 14:  # Top right to top
        x, y = 9, 9 - (i - 11)
    elif i < 20:  # Top to top left
        x, y = 9 - (i - 14), 5
    elif i < 23:  # Top left to left
        x, y = 5, 5 - (i - 20)
    elif i < 29:  # Left to bottom left
        x, y = 5 - (i - 23), 2
    elif i < 32:  # Bottom left to bottom
        x, y = 2, 2 + (i - 29)
    elif i < 38:  # Bottom to bottom right
        x, y = 2 + (i - 32), 8
    elif i < 41:  # Bottom right to center bottom
        x, y = 8, 8 + (i - 38)
    elif i < 47:  # Center bottom to center right
        x, y = 8 + (i - 41), 11
    elif i < 50:  # Center right to center top
        x, y = 11, 11 - (i - 47)
    else:  # Center top to center left
        x, y = 11 - (i - 50), 8
    PATH_POSITIONS.append((x * SQUARE_SIZE + SQUARE_SIZE // 2, y * SQUARE_SIZE + SQUARE_SIZE // 2))

# Home positions for each player
HOME_POSITIONS = [
    [(2, 2), (2, 4), (4, 2), (4, 4)],  # Red
    [(10, 2), (10, 4), (12, 2), (12, 4)],  # Green
    [(10, 10), (10, 12), (12, 10), (12, 12)],  # Blue
    [(2, 10), (2, 12), (4, 10), (4, 12)]  # Yellow
]

# Private path positions for each player (after main path)
PRIVATE_PATHS = [
    [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9), (7, 8)],  # Red
    [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)],  # Green
    [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)],  # Blue
    [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7)]  # Yellow
]

# Center positions
CENTER_POSITIONS = [(7, 7), (7, 9), (9, 7), (9, 9)]

class Piece:
    def __init__(self, player_id, piece_id):
        self.player_id = player_id
        self.piece_id = piece_id
        self.position = 'home'  # 'home', 'path', 'private', 'center'
        self.path_index = -1  # for path and private
        self.home_index = piece_id  # 0-3

    def get_pos(self):
        if self.position == 'home':
            x, y = HOME_POSITIONS[self.player_id][self.home_index]
            return x * SQUARE_SIZE + SQUARE_SIZE // 2, y * SQUARE_SIZE + SQUARE_SIZE // 2
        elif self.position == 'path':
            return PATH_POSITIONS[self.path_index]
        elif self.position == 'private':
            return PRIVATE_PATHS[self.player_id][self.path_index - 52]
        elif self.position == 'center':
            return CENTER_POSITIONS[self.player_id]

    def can_move(self, roll, game):
        if self.position == 'home':
            return roll == 6
        elif self.position == 'path':
            new_index = self.path_index + roll
            if new_index >= 52:
                private_index = new_index - 52
                if private_index > 5:
                    return False  # Can't go beyond center
                # Check if exact
                if private_index == 5:
                    return True
                else:
                    return private_index <= 5
            else:
                return True
        elif self.position == 'private':
            new_index = self.path_index - 52 + roll
            if new_index == 5:
                return True
            elif new_index < 5:
                return True
            else:
                return False
        return False

    def move(self, roll, game):
        if self.position == 'home':
            if roll == 6:
                self.position = 'path'
                self.path_index = self.player_id * 13  # Starting position
        elif self.position == 'path':
            new_index = self.path_index + roll
            if new_index >= 52:
                private_index = new_index - 52
                if private_index == 5:
                    self.position = 'center'
                    self.path_index = -1
                elif private_index < 5:
                    self.position = 'private'
                    self.path_index = 52 + private_index
                # Else can't move
            else:
                self.path_index = new_index
                # Check capture
                for player in game.players:
                    for piece in player.pieces:
                        if piece != self and piece.position == 'path' and piece.path_index == self.path_index:
                            piece.position = 'home'
                            piece.path_index = -1
        elif self.position == 'private':
            new_index = self.path_index - 52 + roll
            if new_index == 5:
                self.position = 'center'
                self.path_index = -1
            elif new_index < 5:
                self.path_index = 52 + new_index

class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.pieces = [Piece(player_id, i) for i in range(4)]
        self.color = PLAYER_COLORS[player_id]

    def has_moves(self, roll, game):
        for piece in self.pieces:
            if piece.can_move(roll, game):
                return True
        return False

    def all_in_center(self):
        return all(piece.position == 'center' for piece in self.pieces)

class Game:
    def __init__(self):
        self.players = [Player(i) for i in range(4)]
        self.current_player = 0
        self.roll = 0
        self.rolled = False
        self.winner = None
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Ludo Game")
        self.clock = pygame.time.Clock()
        self.roll_button = pygame.Rect(650, 350, 100, 50)
        self.selected_piece = None

    def draw_board(self):
        self.screen.fill(WHITE)
        # Draw grid
        for i in range(BOARD_SIZE + 1):
            pygame.draw.line(self.screen, BLACK, (i * SQUARE_SIZE, 0), (i * SQUARE_SIZE, HEIGHT))
            pygame.draw.line(self.screen, BLACK, (0, i * SQUARE_SIZE), (WIDTH, i * SQUARE_SIZE))

        # Color the paths
        # Red path
        for i in range(13):
            idx = (0 * 13 + i) % 52
            x, y = PATH_POSITIONS[idx]
            pygame.draw.circle(self.screen, RED, (x, y), SQUARE_SIZE // 4)
        # Green
        for i in range(13):
            idx = (1 * 13 + i) % 52
            x, y = PATH_POSITIONS[idx]
            pygame.draw.circle(self.screen, GREEN, (x, y), SQUARE_SIZE // 4)
        # Blue
        for i in range(13):
            idx = (2 * 13 + i) % 52
            x, y = PATH_POSITIONS[idx]
            pygame.draw.circle(self.screen, BLUE, (x, y), SQUARE_SIZE // 4)
        # Yellow
        for i in range(13):
            idx = (3 * 13 + i) % 52
            x, y = PATH_POSITIONS[idx]
            pygame.draw.circle(self.screen, YELLOW, (x, y), SQUARE_SIZE // 4)

        # Draw homes
        for p in range(4):
            for pos in HOME_POSITIONS[p]:
                x, y = pos[0] * SQUARE_SIZE, pos[1] * SQUARE_SIZE
                pygame.draw.rect(self.screen, PLAYER_COLORS[p], (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # Draw center
        for pos in CENTER_POSITIONS:
            x, y = pos[0] * SQUARE_SIZE, pos[1] * SQUARE_SIZE
            pygame.draw.rect(self.screen, GRAY, (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # Draw private paths
        for p in range(4):
            for pos in PRIVATE_PATHS[p]:
                x, y = pos[0] * SQUARE_SIZE + SQUARE_SIZE // 2, pos[1] * SQUARE_SIZE + SQUARE_SIZE // 2
                pygame.draw.circle(self.screen, PLAYER_COLORS[p], (x, y), SQUARE_SIZE // 4)

    def draw_pieces(self):
        for player in self.players:
            for piece in player.pieces:
                x, y = piece.get_pos()
                pygame.draw.circle(self.screen, player.color, (x, y), SQUARE_SIZE // 3)
                if piece == self.selected_piece:
                    pygame.draw.circle(self.screen, BLACK, (x, y), SQUARE_SIZE // 3, 3)

    def draw_ui(self):
        # Roll button
        pygame.draw.rect(self.screen, GRAY, self.roll_button)
        font = pygame.font.SysFont(None, 36)
        text = font.render("Roll", True, BLACK)
        self.screen.blit(text, (self.roll_button.x + 20, self.roll_button.y + 10))

        # Current player
        text = font.render(f"Player {self.current_player + 1}'s turn", True, BLACK)
        self.screen.blit(text, (10, 10))

        # Dice roll
        if self.rolled:
            text = font.render(f"Rolled: {self.roll}", True, BLACK)
            self.screen.blit(text, (10, 50))

        # Winner
        if self.winner is not None:
            text = font.render(f"Player {self.winner + 1} wins!", True, BLACK)
            self.screen.blit(text, (WIDTH // 2 - 100, HEIGHT // 2))

    def roll_dice(self):
        self.roll = random.randint(1, 6)
        self.rolled = True

    def next_turn(self):
        self.current_player = (self.current_player + 1) % 4
        self.rolled = False
        self.selected_piece = None

    def handle_click(self, pos):
        if self.roll_button.collidepoint(pos) and not self.rolled:
            self.roll_dice()
            if not self.players[self.current_player].has_moves(self.roll, self):
                self.next_turn()
        elif self.rolled:
            # Check if clicked on a piece
            for piece in self.players[self.current_player].pieces:
                px, py = piece.get_pos()
                if (pos[0] - px) ** 2 + (pos[1] - py) ** 2 < (SQUARE_SIZE // 3) ** 2:
                    if piece.can_move(self.roll, self):
                        self.selected_piece = piece
                        piece.move(self.roll, self)
                        if self.players[self.current_player].all_in_center():
                            self.winner = self.current_player
                        if self.roll != 6:
                            self.next_turn()
                        else:
                            self.rolled = False
                            self.selected_piece = None
                        break

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.draw_board()
            self.draw_pieces()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()