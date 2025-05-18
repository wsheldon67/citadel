#region ---------------------------------------------- To-Do ------------------
#Update ConfigUI to buttons instead of text input.


#region ------------------------------------------ Initialization------------------
import pygame
from collections import deque
import math

pygame.init()
WIDTH, HEIGHT = 1000, 700  # window size
UI_HEIGHT = int(HEIGHT * 0.15)
TILE_SIZE = 40
FONT = pygame.font.Font(None, 30)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Citadel - Board Setup")
REMOVAL_HEIGHT = 100
#endregion

#region------------------------------------------ Piece Zone UI ------------------
# Zones for piece selection phase
personal_area = pygame.Rect(0, 0, int(WIDTH * 0.25), HEIGHT - REMOVAL_HEIGHT)
offered_area = pygame.Rect(int(WIDTH * 0.25), 0, int(WIDTH * 0.5), HEIGHT - REMOVAL_HEIGHT)
community_area = pygame.Rect(int(WIDTH * 0.75), 0, int(WIDTH * 0.25), HEIGHT - REMOVAL_HEIGHT)
removal_zone = pygame.Rect(0, HEIGHT - REMOVAL_HEIGHT, WIDTH, REMOVAL_HEIGHT)

# UI Areas for Game Phase
personal_stash_area = pygame.Rect(150, HEIGHT - 75, WIDTH - 300, 75)
community_stash_area = pygame.Rect(WIDTH - 150, 0, 150, HEIGHT)
graveyard_area = pygame.Rect(0, 0, 150, HEIGHT)
#endregion

#region---------------------------------- Game Configuration Defaults ------------------
num_land_tiles = 5
num_personal_pool = 3
num_community_pool = 3
max_stash_capacity = 3

current_player = 1
selection_message = ""
finish_button_rect = pygame.Rect(0, 0, 0, 0)
toggle_button_rect = pygame.Rect(WIDTH - 170, 10, 150, 40)
#endregion

#region-----------------------------------------------Board Classes ------------------
    
class Citadel:
    def __init__(self, position:tuple[int,int], owner:int):
        self.position = position
        self.owner = owner

    def __repr__(self):
        return f"Citadel({self.position}, Owner: {self.owner})"

#endregion

#region ----------------------------------------   Piece Functions ------------------
def handle_interaction(capturing_piece, turtle):
    """
    This function handles the interaction when a piece tries to interact with a Turtle.
    - Capturing piece stays in place.
    - The Turtle goes to the graveyard.
    """
    if isinstance(capturing_piece, Piece) and isinstance(turtle, Piece):
        if capturing_piece.interact_with_turtle(turtle):
            print(f"{capturing_piece.name} interacts with {turtle.name}.")
            return True
    return False

class Land:
    def __init__(self, position:tuple[int,int]|None=None):
        self.position = position

class Piece:
    def __init__(self, name, owner, position:tuple[int,int]|None=None, ):
        self.name = name
        self.position = position
        self.owner = owner

    def can_be_moved_to():

    def get_valid_moves():

    def highlight_valid_tiles():

    def move(self, new_position, board):
        allowed_moves = [
            (self.position[0] + 1, self.position[1]),  # Right
            (self.position[0] - 1, self.position[1]),  # Left
            (self.position[0], self.position[1] + 1),  # Down
            (self.position[0], self.position[1] - 1),  # Up
        ]
        if new_position in allowed_moves and (board[new_position] in [Land, Turtle]):
            return True
        return False

    def capture(self, target_piece):
        if target_piece.owner != self.owner:
            graveyard.append(target_piece)
            return True
        return False

    def ability(self, board):
        pass

    def interact_with_turtle(self, turtle):
        if self.move(turtle.position, board):
            graveyard.append(turtle)
            return True
        return False

    def place_piece(self, piece, x, y, board):
        if piece.can_be_placed_at(x, y, board):
            self.position = (x, y)

    def can_be_placed_at(self, x, y, board):
        print(f"[DEBUG] Checking if {self.name} can be placed at ({x}, {y}).")

        if (x, y) in board:
            if board.has((x,y),Turtle)or board.has((x,y),Land): # Land tile
                print(f"[DEBUG] {self.name} can be placed on land tile at ({x}, {y}).")
                for citadel in citadels:
                    if self.owner == citadel["owner"] and is_adjacent(citadel["pos"][0], citadel["pos"][1], x, y):
                        print(f"[DEBUG] {self.name} can be placed near its own citadel.")
                
                return True
        print(f"[DEBUG] {self.name} CANNOT be placed at ({x}, {y}).")
        return False




class Knight(Piece):
    def move(self, new_position, board):
        pass

    def capture(self, target_piece):
        pass

class Bird(Piece):
    def move(self, new_position, board):
        pass

    def capture(self, target_piece):
        pass

class Turtle(Piece):
    def move(self, new_position, board):
        pass

    def capture(self, target_piece):
        pass

class Rabbit(Piece):
    def move(self, new_position, board):
        pass

    def capture(self, target_piece):
        pass

class Builder(Piece):
    def move(self, new_position, board):
        pass

    def capture(self, target_piece):
        pass

class Bomber(Piece):
    def move(self, new_position, board):
        pass

    def capture(self, target_piece):
        pass

class Necromancer(Piece):
    def move(self, new_position, board):
        pass

    def capture(self, target_piece):
        pass

class Assassin(Piece):
    def move(self, new_position, board):
        pass

    def capture(self, target_piece):
        pass


PIECE_REGISTRY = {
    "Knight": Knight,
    "Bird": Bird,
    "Turtle": Turtle,
    "Rabbit": Rabbit,
    "Builder": Builder,
    "Bomber": Bomber,
    "Necromancer": Necromancer,
    "Assassin": Assassin
}

# Debugging Code
for piece_name, piece_class in PIECE_REGISTRY.items():
    if hasattr(piece_class, 'can_be_placed_at'):
        print(f"{piece_name}: has 'can_be_placed_at()' method.")
    else:
        print(f"{piece_name}: MISSING 'can_be_placed_at()' method.")

#endregion

#region------------------------------------ Piece Selection UI Setup ------------------
available_types = ["Bird", "Knight", "Turtle", "Rabbit", "Builder", "Bomber", "Necromancer", "Assassin"]
offered_piece_width = 150
offered_piece_height = 50
padding_x = 20
padding_y = 20
num_columns = 2
num_rows = math.ceil(len(available_types) / num_columns)
total_width = num_columns * offered_piece_width + (num_columns + 1) * padding_x
total_height = num_rows * offered_piece_height + (num_rows + 1) * padding_y
start_x = offered_area.x + (offered_area.width - total_width) // 2 + padding_x
start_y = offered_area.y + (offered_area.height - total_height) // 2 + padding_y


offered_pieces: list[Piece] = []
for index, piece_name in enumerate(available_types):
    col = index % num_columns
    row = index // num_columns
    rect = pygame.Rect(
        start_x + col * (offered_piece_width + padding_x),
        start_y + row * (offered_piece_height + padding_y),
        offered_piece_width,
        offered_piece_height
    )
    piece_class = PIECE_REGISTRY[piece_name](piece_name, owner=current_player)
    offered_pieces.append({"piece": piece_class, "rect": rect})




#endregion

#region ------------------------------------------- Dictionaries ------------------
personal_stash: list[Piece] = []    # Personal pieces chosen
community_stash = []   # Community pieces chosen
graveyard = []         # Pieces captured

class Board:
    def __init__(self):
        self.tiles:list[Land,Piece,Citadel] = []  # Dictionary to store tile positions and types

    def __getitem__(self, key:tuple[int,int]) -> list[Land|Piece|Citadel]:
        res= []
        for tile in self.tiles:
            if tile.position == key:
                res.append(tile)
        return res

    def __contains__(self, key):
        return key in self.tiles

    def has(self,position,entity):
        entities = self.__getitem__(position)
        for placed in entities:
            if isinstance(placed, entity):
                return True
        return False


#endregion

#region----------------------------------------------- Colors ------------------
WATER_COLOR = (0, 0, 128)
LAND_COLOR = (34, 139, 34)
CITADEL_COLOR = (255, 255, 0)
GRID_COLOR = (255, 255, 255)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_MOVE_COLOR = (255, 255, 0)    # Yellow
HIGHLIGHT_CAPTURE_COLOR = (255, 0, 0)     # Red
PLAYER1_COLOR = (255, 165, 0)  # Orange
PLAYER2_COLOR = (128, 0, 128)  # Purple
#endregion

#region------------------------------------------- Misc. Variables ------------------
piece_selection_done = False
land_tiles_remaining = 10
placing_land = True
game_message = "Place land tiles."
selected_piece = None


# Center a 3x3 grid initially
grid_center_x = WIDTH // 2 // TILE_SIZE
grid_center_y = (HEIGHT - 100) // 2 // TILE_SIZE
min_x, max_x = grid_center_x - 1, grid_center_x + 1
min_y, max_y = grid_center_y - 1, grid_center_y + 1
#endregion

#region ------------------------------------------ Helper Functions ------------------
def switch_player():
    global current_player
    current_player = 2 if current_player == 1 else 1

def expand_board(x, y):
    global min_x, max_x, min_y, max_y
    if x <= min_x:
        min_x = x - 1
    if x >= max_x:
        max_x = x + 1
    if y <= min_y:
        min_y = y - 1
    if y >= max_y:
        max_y = y + 1

def is_adjacent(x, y):
    adjacent_positions = [
        (x-1, y), (x+1, y),
        (x, y-1), (x, y+1),
        (x-1, y-1), (x+1, y-1),
        (x-1, y+1), (x+1, y+1)
    ]
    return any(pos in board for pos in adjacent_positions)

def is_connected_to_existing_citadels(x, y):
    visited = set()
    queue = deque([(x, y)])

    while queue:
        cx, cy = queue.popleft()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in board and board[(nx, ny)] == Land and (nx, ny) not in visited:
                queue.append((nx, ny))

    for citadel in citadels:
        cx, cy = citadel["pos"]
        if (cx, cy) not in visited:
            return False
    return True

#endregion

#region ---------------------------------------- Placement Functions ------------------
def place_land_tile(x, y):
    global land_tiles_remaining, placing_land, game_message
    if (x, y) in board:
        return
    if not board or is_adjacent(x, y):
        board[(x, y)] = Land
        land_tiles_remaining -= 1
        expand_board(x, y)
        if land_tiles_remaining == 0:
            placing_land = False
            game_message = "All land tiles placed! Click to place Citadels."
    else:
        game_message = "Invalid placement! Land must touch existing land."

def place_citadel(x, y):
    global game_message, piece_selection_done, current_player

    if (x, y) not in board or board[(x, y)] != Land:
        game_message = "Citadel must be placed on a land tile!"
        return

    if any(citadel["pos"] == (x, y) for citadel in citadels):
        return
    
    for citadel in citadels:
        cx, cy = citadel["pos"]
        if abs(cx - x) <= 1 and abs(cy - y) <= 1:
            game_message = "Citadel placement is too close to another citadel!"
            return

    if len(citadels) == 0:
        citadels.append({"pos": (x, y), "owner": current_player})
        game_message = "First Citadel placed! Place the second Citadel."
        switch_player()
    
    elif len(citadels) == 1:
        if not is_connected_to_existing_citadels(x, y):
            game_message = "Your citadel must be connected to the other citadels!"
            return

        citadels.append({"pos": (x, y), "owner": current_player})
        game_message = "Both Citadels placed! Confirm board layout."
        confirm_board_layout()
        piece_selection_phase()
        piece_selection_done = True
        start_game_phase()



#endregion

#region ----------------------------------------- Drawing Functions ------------------

def draw_board():
    global choice_highlight_tiles
    screen.fill(WATER_COLOR)
    grid_min_x = min_x - 3
    grid_max_x = max_x + 3
    grid_min_y = min_y - 3
    grid_max_y = max_y + 3
    grid_width = (grid_max_x - grid_min_x + 1) * TILE_SIZE
    grid_height = (grid_max_y - grid_min_y + 1) * TILE_SIZE
    offset_x = (WIDTH - grid_width) // 2
    offset_y = (HEIGHT - UI_HEIGHT - grid_height) // 2

    for x in range(grid_min_x, grid_max_x + 1):
        for y in range(grid_min_y, grid_max_y + 1):
            color = LAND_COLOR if (x, y) in board else WATER_COLOR
            pygame.draw.rect(screen, color, ((x - grid_min_x) * TILE_SIZE + offset_x,
                                               (y - grid_min_y) * TILE_SIZE + offset_y,
                                               TILE_SIZE, TILE_SIZE))
    
    for x in range(offset_x, offset_x + grid_width + 1, TILE_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, offset_y), (x, offset_y + grid_height))
    for y in range(offset_y, offset_y + grid_height + 1, TILE_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (offset_x, y), (offset_x + grid_width, y))
    pygame.draw.rect(screen, GRID_COLOR, (offset_x, offset_y, grid_width, grid_height), 3)
    
    for citadel in citadels:
        cx, cy = citadel["pos"]
        citadel_color = PLAYER1_COLOR if citadel["owner"] == 1 else PLAYER2_COLOR
        pygame.draw.rect(screen, citadel_color, ((cx - grid_min_x) * TILE_SIZE + offset_x,
                                                   (cy - grid_min_y) * TILE_SIZE + offset_y,
                                                   TILE_SIZE, TILE_SIZE))
        text_surface = FONT.render("C", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=((cx - grid_min_x) * TILE_SIZE + offset_x + TILE_SIZE//2,
                                                   (cy - grid_min_y) * TILE_SIZE + offset_y + TILE_SIZE//2))
        screen.blit(text_surface, text_rect)
    
    # Updated drawing of placed pieces:
    for (x, y), data in placed_pieces.items():
        if data["type"] == "Turtle" and "mounted" in data:
            turtle_color = PLAYER1_COLOR if data["owner"] == 1 else PLAYER2_COLOR
            turtle_text = FONT.render("T", True, turtle_color)
            mount_data = data["mounted"]
            mount_color = PLAYER1_COLOR if mount_data["owner"] == 1 else PLAYER2_COLOR
            mount_text = FONT.render(mount_data["type"][0], True, mount_color)
            # Draw the turtle letter at one position and overlay the mounted piece slightly offset.
            screen.blit(turtle_text, ((x - grid_min_x) * TILE_SIZE + offset_x + TILE_SIZE//4,
                                      (y - grid_min_y) * TILE_SIZE + offset_y + TILE_SIZE//4))
            screen.blit(mount_text, ((x - grid_min_x) * TILE_SIZE + offset_x + TILE_SIZE//2,
                                     (y - grid_min_y) * TILE_SIZE + offset_y + TILE_SIZE//2))
        else:
            piece_color = PLAYER1_COLOR if data["owner"] == 1 else PLAYER2_COLOR
            piece_text = FONT.render(str(data["type"])[0], True, piece_color)
            screen.blit(piece_text, ((x - grid_min_x) * TILE_SIZE + offset_x + TILE_SIZE//3,
                                     (y - grid_min_y) * TILE_SIZE + offset_y + TILE_SIZE//3))
    
    if piece_selection_done:
        draw_graveyard()
        draw_personal_stash_ui()
        draw_community_stash_ui()
    draw_ui()
    pygame.display.flip()

def draw_ui(): #board creation UI #done
    if not piece_selection_done:
        ui_background = pygame.Rect(0, HEIGHT - UI_HEIGHT, WIDTH, UI_HEIGHT)
        pygame.draw.rect(screen, (50, 50, 50), ui_background)
        tile_text = f"Land Tiles Remaining: {land_tiles_remaining}" if placing_land else "Placing Citadels"
        tile_surface = FONT.render(tile_text, True, TEXT_COLOR)
        screen.blit(tile_surface, (20, HEIGHT - UI_HEIGHT + 20))
        msg_surface = FONT.render(game_message, True, TEXT_COLOR)
        screen.blit(msg_surface, (20, HEIGHT - UI_HEIGHT + 50))

def draw_selection_screen(): #piece selection UI #done
    screen.fill((50, 50, 50))
    pygame.draw.rect(screen, (80, 80, 80), personal_area)
    pygame.draw.rect(screen, (100, 100, 100), offered_area)
    pygame.draw.rect(screen, (80, 80, 80), community_area)
    pygame.draw.rect(screen, (150, 0, 0), removal_zone)
    p_label = FONT.render("Personal Stash", True, (255, 255, 255))
    screen.blit(p_label, p_label.get_rect(center=(personal_area.centerx, personal_area.y + 20)))
    o_label = FONT.render("Offered Pieces", True, (255, 255, 255))
    screen.blit(o_label, o_label.get_rect(center=(offered_area.centerx, offered_area.y + 20)))
    c_label = FONT.render("Community Stash", True, (255, 255, 255))
    screen.blit(c_label, c_label.get_rect(center=(community_area.centerx, community_area.y + 20)))
    r_label = FONT.render("Trash", True, (255, 255, 255))
    screen.blit(r_label, r_label.get_rect(center=(removal_zone.centerx, removal_zone.y + 20)))
    
    for item in offered_pieces:
        pygame.draw.rect(screen, (100, 100, 200), item["rect"])
        piece_class = item["piece"]
        piece_name = piece_class.name
        piece_text = FONT.render(piece_name, True, (255, 255, 255))
        screen.blit(piece_text, (item["rect"].x + 10, item["rect"].y + 10))
    
    for i, piece in enumerate(personal_stash):
        rect = pygame.Rect(personal_area.x + 10, personal_area.y + 50 + i * 60, 150, 50)
        pygame.draw.rect(screen, (120, 120, 220), rect)
        
        piece_name = piece.name
        text_surface = FONT.render(piece_name, True, (255, 255, 255))
        screen.blit(text_surface, text_surface.get_rect(center=rect.center))

    for i, piece in enumerate(community_stash):
        rect = pygame.Rect(community_area.x + 10, community_area.y + 50 + i * 60, 150, 50)
        pygame.draw.rect(screen, (120, 120, 220), rect)
        piece_name = piece.name
        text_surface = FONT.render(piece_name, True, (255, 255, 255))
        screen.blit(text_surface, text_surface.get_rect(center=rect.center))
    
    if dragging_piece:
        pygame.draw.rect(screen, (200, 100, 100), dragging_piece["rect"])
        drag_piece_name = dragging_piece["piece"].name
        drag_text = FONT.render(drag_piece_name, True, (255, 255, 255))
        screen.blit(drag_text, drag_text.get_rect(center=dragging_piece["rect"].center))

    if selection_message:
        msg_surface = FONT.render(selection_message, True, (255, 255, 0))
        screen.blit(msg_surface, msg_surface.get_rect(center=(removal_zone.centerx, removal_zone.y + 20)))
    if len(personal_stash) >= max_stash_capacity and len(community_stash) >= max_stash_capacity:
        global finish_button_rect
        finish_button = pygame.Rect(removal_zone.centerx - 125, removal_zone.centery - 15, 250, 50)
        pygame.draw.rect(screen, (0, 200, 0), finish_button)
        finish_text = FONT.render("Confirm Selection", True, (0, 0, 0))
        screen.blit(finish_text, finish_text.get_rect(center=finish_button.center))
        finish_button_rect = finish_button
    pygame.display.flip()

def draw_graveyard():
    pygame.draw.rect(screen, (30, 30, 30), graveyard_area)
    grave_label = FONT.render("Graveyard", True, (255, 255, 255))
    screen.blit(grave_label, grave_label.get_rect(center=(graveyard_area.centerx, 30)))
    y_offset = 60
    for piece in graveyard:
        piece_name = piece.name 
        text = FONT.render(piece_name, True, (200, 200, 200))
        screen.blit(text, (10, y_offset))
        y_offset += 30

def draw_personal_stash_ui():
    pygame.draw.rect(screen, (70, 70, 70), personal_stash_area)
    if personal_stash:
        piece_width = personal_stash_area.width / len(personal_stash)
        for i, piece in enumerate(personal_stash):
            piece_x = personal_stash_area.x + i * piece_width + piece_width / 2
            piece_name = piece.name
            text = FONT.render(piece_name, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(piece_x, personal_stash_area.centery))
            screen.blit(text, text_rect)
            pygame.draw.rect(screen, (0, 255, 0),
                             (personal_stash_area.x + i * piece_width, personal_stash_area.y, piece_width, personal_stash_area.height), 1)
    else:
        stash_text = "Personal Pool: (empty)"
        text_surface = FONT.render(stash_text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(midleft=(personal_stash_area.x + 10, personal_stash_area.centery))
        screen.blit(text_surface, text_rect)

def draw_community_stash_ui():
    global toggle_button_rect
    pygame.draw.rect(screen, (50, 50, 50), community_stash_area)

    turn_text = FONT.render(f"Player {current_player}'s Turn", True, TEXT_COLOR)
    turn_rect = turn_text.get_rect(center=(community_stash_area.centerx, 20))
    screen.blit(turn_text, turn_rect)

    toggle_button_width = 100
    toggle_button_height = 40
    toggle_button_x = community_stash_area.centerx - toggle_button_width // 2
    toggle_button_y = turn_rect.bottom + 15
    toggle_button_rect = pygame.Rect(toggle_button_x, toggle_button_y, toggle_button_width, toggle_button_height)
    pygame.draw.rect(screen, (255, 0, 0), toggle_button_rect, 4)
    toggle_text = FONT.render("Toggle", True, TEXT_COLOR)
    screen.blit(toggle_text, toggle_text.get_rect(center=toggle_button_rect.center))

    separator_y = toggle_button_rect.bottom + 20
    pygame.draw.line(screen, GRID_COLOR, (community_stash_area.x, separator_y),
                     (community_stash_area.x + community_stash_area.width, separator_y), 2)

    community_label = FONT.render("Community", True, TEXT_COLOR)
    pool_font = pygame.font.Font(None, 30)
    pool_font.set_underline(True)
    pool_label = pool_font.render("Pool", True, TEXT_COLOR)
    community_label_rect = community_label.get_rect(center=(community_stash_area.centerx, separator_y + 30))
    pool_label_rect = pool_label.get_rect(center=(community_stash_area.centerx, community_label_rect.bottom + 20))
    screen.blit(community_label, community_label_rect)
    screen.blit(pool_label, pool_label_rect)

    y_offset = pool_label_rect.bottom + 20
    global community_stash_base_y
    community_stash_base_y = y_offset
    for piece in community_stash:
        piece_name = piece.name
        text = FONT.render(piece_name, True, TEXT_COLOR)
        text_rect = text.get_rect(center=(community_stash_area.centerx, y_offset + 15))
        screen.blit(text, text_rect)
        y_offset += 30

def confirm_board_layout(): #done
    # Draw the board once and store it on-screen.
    draw_board()
    pygame.display.flip()

    confirming = True
    # Define a confirmation zone (a bar at the bottom of the screen)
    confirm_zone = pygame.Rect(0, HEIGHT - REMOVAL_HEIGHT, WIDTH, REMOVAL_HEIGHT)
    # Move the confirm button more to the right: 
    confirm_button = pygame.Rect(WIDTH - 250, confirm_zone.y + 10, 200, confirm_zone.height - 20)
    
    while confirming:
        # Instead of redrawing the entire board, only redraw the confirmation zone on top.
        pygame.draw.rect(screen, (50, 50, 50), confirm_zone)
        
        # Draw the confirmation message.
        msg = FONT.render("Confirm Board Layout", True, (255, 255, 255))
        msg_rect = msg.get_rect(center=(WIDTH // 2, confirm_zone.y + 15))
        screen.blit(msg, msg_rect)
        
        # Draw the confirm button.
        pygame.draw.rect(screen, (0, 200, 0), confirm_button)
        btn_text = FONT.render("Confirm", True, (0, 0, 0))
        btn_rect = btn_text.get_rect(center=confirm_button.center)
        screen.blit(btn_text, btn_rect)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if confirm_button.collidepoint(event.pos):
                    confirming = False
        
        # Increase delay to reduce any visual flicker.
        pygame.time.wait(100)

#endregion

#region------------------------------------------ Mouse Click Handler ------------------

def handle_mouse_click(pos, player):
    global selected_piece, current_player, game_message, community_stash_base_y, choice_highlight_tiles
    x, y = pos

    # Toggle button for testing.
    if toggle_button_rect.collidepoint(pos):
        switch_player()
        return

    # Calculate grid coordinates based on the expanded grid.
    grid_min_x = min_x - 3
    grid_max_x = max_x + 3
    grid_min_y = min_y - 3
    grid_max_y = max_y + 3
    grid_width = (grid_max_x - grid_min_x + 1) * TILE_SIZE
    grid_height = (grid_max_y - grid_min_y + 1) * TILE_SIZE
    offset_x = (WIDTH - grid_width) // 2
    offset_y = (HEIGHT - UI_HEIGHT - grid_height) // 2
    grid_x = (x - offset_x) // TILE_SIZE + grid_min_x
    grid_y = (y - offset_y) // TILE_SIZE + grid_min_y

    # Land placement phase.
    if placing_land:
        if (grid_x, grid_y) not in placed_pieces:
            place_land_tile(grid_x, grid_y)
        return

    # Citadel placement phase.
    elif len(citadels) < 2:
        if (grid_x, grid_y) in board and (grid_x, grid_y) not in placed_pieces:
            place_citadel(grid_x, grid_y)
        return
    
    elif piece_selection_done:
        if selected_piece:
            # Pass the board as an argument to can_be_placed_at
            if selected_piece:
                print(f"[DEBUG] Selected Piece Type: {type(selected_piece)}")
                print(f"[DEBUG] Selected Piece: {selected_piece.name}")
                print(f"[DEBUG] Trying to call can_be_placed_at() with: ({grid_x}, {grid_y}, board)")

                if hasattr(selected_piece, 'can_be_placed_at'):
                    print("[DEBUG] The selected piece has 'can_be_placed_at()' method.")
                else:
                    print("[DEBUG] The selected piece is missing 'can_be_placed_at()' method.")

                if selected_piece.can_be_placed_at(grid_x, grid_y, board):
                    print("[DEBUG] Placement successful.")
                else:
                    print("[DEBUG] Placement failed.")

                # Place the piece if valid
                place_piece(selected_piece, grid_x, grid_y, board)
                # After placing the piece, switch to the next player's turn
                switch_player()
            else:
                game_message = f"{selected_piece.name} cannot be placed here!"

    # Stash selection: Check stash areas first.
    if not piece_selection_done:
        for index, item in enumerate(offered_pieces):
            if item["rect"].collidepoint(x, y):
                selected_index = index
                selected_piece_class = item["piece"]  # This is a class reference, not an instance

                if isinstance(selected_piece_class, type) and issubclass(selected_piece_class, Piece):
                    # ✅ Create an instance of the selected piece class
                    selected_piece = selected_piece_class(name=selected_piece_class.name, position=(grid_x, grid_y), owner=current_player)
                    print(f"[DEBUG] Successfully created piece instance: {selected_piece.name} of type {type(selected_piece)}")
                else:
                    print(f"[DEBUG] Error: {selected_piece_class} is not a valid Piece class.")

                place_piece(selected_piece, grid_x, grid_y, board)
                break



    else:
        # In game phase, use updated stash UI areas.
        if personal_stash_area.collidepoint(x, y):
            if personal_stash:
                piece_width = personal_stash_area.width / len(personal_stash)
                relative_x = x - personal_stash_area.x
                index = int(relative_x // piece_width)
                index = min(index, len(personal_stash) - 1)
                selected_piece = personal_stash[index]
            return
        elif community_stash_area.collidepoint(x, y):
            index = int((y - community_stash_base_y) // 30)
            if 0 <= index < len(community_stash):
                selected_piece = community_stash[index]
            return

#endregion

#region ------------------------------------------ Phase Functions ------------------
def configuration_phase():
    # Defaults
    land_input = "10"
    personal_input = "3"
    community_input = "3"
    
    # Define rectangles for input fields and labels
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    field_width = 100
    field_height = 40

    # Input field positions (to the right of their labels)
    land_field_rect = pygame.Rect(center_x + 50, center_y - 120, field_width, field_height)
    personal_field_rect = pygame.Rect(center_x + 50, center_y - 40, field_width, field_height)
    community_field_rect = pygame.Rect(center_x + 50, center_y + 40, field_width, field_height)

    # Label positions (shifted to the left for better spacing)
    land_label_pos = (center_x - 200, center_y - 120)
    personal_label_pos = (center_x - 200, center_y - 40)
    community_label_pos = (center_x - 200, center_y + 40)

    # Confirm button
    confirm_button = pygame.Rect(center_x - 75, center_y + 120, 150, 50)

    active_field = None  # Can be "land", "personal", or "community"

    configuring = True
    global num_land_tiles, num_personal_pool, num_community_pool
    # Set defaults in globals (if desired)
    num_land_tiles = int(land_input)
    num_personal_pool = int(personal_input)
    num_community_pool = int(community_input)

    while configuring:
        screen.fill((30, 30, 30))
        
        # Draw labels
        land_label = FONT.render("Land Tiles:", True, (255, 255, 255))
        personal_label = FONT.render("Personal Pool Pieces:", True, (255, 255, 255))
        community_label = FONT.render("Community Pool Pieces:", True, (255, 255, 255))
        screen.blit(land_label, land_label_pos)
        screen.blit(personal_label, personal_label_pos)
        screen.blit(community_label, community_label_pos)
        
        # Draw input fields (with a border to indicate active field)
        pygame.draw.rect(screen, (255, 255, 255), land_field_rect, 2 if active_field=="land" else 1)
        pygame.draw.rect(screen, (255, 255, 255), personal_field_rect, 2 if active_field=="personal" else 1)
        pygame.draw.rect(screen, (255, 255, 255), community_field_rect, 2 if active_field=="community" else 1)
        
        # Render current text inside each field
        land_text = FONT.render(land_input, True, (255, 255, 255))
        personal_text = FONT.render(personal_input, True, (255, 255, 255))
        community_text = FONT.render(community_input, True, (255, 255, 255))
        screen.blit(land_text, (land_field_rect.x+5, land_field_rect.y+5))
        screen.blit(personal_text, (personal_field_rect.x+5, personal_field_rect.y+5))
        screen.blit(community_text, (community_field_rect.x+5, community_field_rect.y+5))
        
        # Draw confirm button
        pygame.draw.rect(screen, (0, 0, 200), confirm_button)
        confirm_text = FONT.render("Confirm", True, (255, 255, 255))
        screen.blit(confirm_text, confirm_text.get_rect(center=confirm_button.center))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if click is in any input field; if so, set it active
                if land_field_rect.collidepoint(event.pos):
                    active_field = "land"
                elif personal_field_rect.collidepoint(event.pos):
                    active_field = "personal"
                elif community_field_rect.collidepoint(event.pos):
                    active_field = "community"
                elif confirm_button.collidepoint(event.pos):
                    # When confirming, update the global values and exit configuration
                    try:
                        num_land_tiles = int(land_input)
                        num_personal_pool = int(personal_input)
                        num_community_pool = int(community_input)
                    except ValueError:
                        # If conversion fails, keep defaults
                        pass
                    configuring = False
                else:
                    active_field = None
            elif event.type == pygame.KEYDOWN:
                if active_field is not None:
                    # Accept only numeric input and backspace
                    if event.key == pygame.K_BACKSPACE:
                        if active_field == "land":
                            land_input = land_input[:-1]
                        elif active_field == "personal":
                            personal_input = personal_input[:-1]
                        elif active_field == "community":
                            community_input = community_input[:-1]
                    else:
                        if event.unicode.isdigit():
                            if active_field == "land":
                                land_input += event.unicode
                            elif active_field == "personal":
                                personal_input += event.unicode
                            elif active_field == "community":
                                community_input += event.unicode
        
        pygame.time.wait(50)

def piece_selection_phase():
    global dragging_piece, drag_offset_x, drag_offset_y, finish_button_rect, selection_message
    selection_running = True
    dragging_piece = None
    drag_offset_x = 0
    drag_offset_y = 0
    selection_message = ""
    while selection_running:
        draw_selection_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                selection_running = False
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                dragging_piece = None
                # Check if a piece from personal stash is dragged.
                for i, piece in enumerate(personal_stash):
                    rect = pygame.Rect(personal_area.x + 10, personal_area.y + 50 + i * 60, 150, 50)
                    if rect.collidepoint(mouse_pos):
                        dragging_piece = {"piece": piece, "rect": rect.copy()}
                        drag_offset_x = mouse_pos[0] - rect.x
                        drag_offset_y = mouse_pos[1] - rect.y
                        personal_stash.pop(i)
                        break
                if not dragging_piece:
                    for i, piece in enumerate(community_stash):
                        rect = pygame.Rect(community_area.x + 10, community_area.y + 50 + i * 60, 150, 50)
                        if rect.collidepoint(mouse_pos):
                            dragging_piece = {"piece": piece, "rect": rect.copy()}
                            drag_offset_x = mouse_pos[0] - rect.x
                            drag_offset_y = mouse_pos[1] - rect.y
                            community_stash.pop(i)
                            break
                if not dragging_piece:
                    for item in offered_pieces:
                        if item["rect"].collidepoint(mouse_pos):
                            dragging_piece = {"piece": item["piece"], "rect": item["rect"].copy()}
                            drag_offset_x = mouse_pos[0] - item["rect"].x
                            drag_offset_y = mouse_pos[1] - item["rect"].y
                            break
                if len(personal_stash) >= max_stash_capacity and len(community_stash) >= max_stash_capacity:
                    if finish_button_rect.collidepoint(mouse_pos):
                        selection_running = False
                        return
            elif event.type == pygame.MOUSEMOTION:
                if dragging_piece:
                    dragging_piece["rect"].x = event.pos[0] - drag_offset_x
                    dragging_piece["rect"].y = event.pos[1] - drag_offset_y
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging_piece:
                    mouse_pos = event.pos
                    if personal_area.collidepoint(mouse_pos):
                        if len(personal_stash) < max_stash_capacity:
                            personal_stash.append(dragging_piece["piece"])
                            selection_message = ""
                        else:
                            selection_message = "Personal stash is full!"
                    elif community_area.collidepoint(mouse_pos):
                        if len(community_stash) < max_stash_capacity:
                            community_stash.append(dragging_piece["piece"])
                            selection_message = ""
                        else:
                            selection_message = "Community stash is full!"
                    elif removal_zone.collidepoint(mouse_pos):
                        selection_message = ""
                        print(f"Removed {dragging_piece['piece']}")
                    dragging_piece = None
        pygame.display.flip()

def start_game_phase():
    global game_message
    print("Starting game phase...")
    game_message = "Piece selection complete! Starting game phase..."
    main_running = True
    while main_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                main_running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_click(event.pos, player=current_player)
        draw_board()
        pygame.display.flip()
    pygame.quit()

#endregion

#region ------------------------------------------ Main Game Loop ------------------
# Run the configuration phase once.
configuration_phase()

#Update dependent variables:
land_tiles_remaining = num_land_tiles
max_stash_capacity = num_personal_pool

# Then start the main game loop.
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_mouse_click(event.pos, player=current_player)
    draw_board()
    pygame.display.flip()
pygame.quit()
#endregion