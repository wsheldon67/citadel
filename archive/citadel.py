import pygame
from collections import deque
import math

# ------------------ Pygame Setup ------------------
pygame.init()
WIDTH, HEIGHT = 1000, 700  # window size
UI_HEIGHT = int(HEIGHT * 0.15)
TILE_SIZE = 40
FONT = pygame.font.Font(None, 30)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Citadel - Board Setup")

REMOVAL_HEIGHT = 100
# Zones for piece selection phase
personal_area = pygame.Rect(0, 0, int(WIDTH * 0.25), HEIGHT - REMOVAL_HEIGHT)
offered_area = pygame.Rect(int(WIDTH * 0.25), 0, int(WIDTH * 0.5), HEIGHT - REMOVAL_HEIGHT)
community_area = pygame.Rect(int(WIDTH * 0.75), 0, int(WIDTH * 0.25), HEIGHT - REMOVAL_HEIGHT)
removal_zone = pygame.Rect(0, HEIGHT - REMOVAL_HEIGHT, WIDTH, REMOVAL_HEIGHT)
graveyard_area = pygame.Rect(0, 0, 150, HEIGHT)

# UI Areas for Game Phase
personal_stash_area = pygame.Rect(150, HEIGHT - 75, WIDTH - 300, 75)
community_stash_area = pygame.Rect(WIDTH - 150, 0, 150, HEIGHT)

# Game configuration parameters (defaults for both players)
num_land_tiles = 5
num_personal_pool = 3
num_community_pool = 3
max_stash_capacity = 3

selection_message = ""
finish_button_rect = pygame.Rect(0, 0, 0, 0)
toggle_button_rect = pygame.Rect(WIDTH - 170, 10, 150, 40)

# Offered pieces configuration (for piece selection)
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

offered_pieces = []
for index, piece in enumerate(available_types):
    col = index % num_columns
    row = index // num_columns
    rect = pygame.Rect(
        start_x + col * (offered_piece_width + padding_x),
        start_y + row * (offered_piece_height + padding_y),
        offered_piece_width,
        offered_piece_height
    )
    offered_pieces.append({"piece": piece, "rect": rect})

# ------------------ Data Structures ------------------
personal_stash = []    # Personal pieces chosen
community_stash = []   # Community pieces chosen
graveyard = []         # Pieces captured

# ------------------ Colors ------------------
WATER_COLOR = (0, 0, 128)
LAND_COLOR = (34, 139, 34)
CITADEL_COLOR = (255, 255, 0)
GRID_COLOR = (255, 255, 255)
TEXT_COLOR = (255, 255, 255)
HIGHLIGHT_MOVE_COLOR = (255, 255, 0)    # Yellow
HIGHLIGHT_CAPTURE_COLOR = (255, 0, 0)     # Red
PLAYER1_COLOR = (255, 165, 0)  # Orange
PLAYER2_COLOR = (128, 0, 128)  # Purple

# ------------------ Game Variables ------------------
piece_selection_done = False
board = {}       # {(x, y): "L"}
citadels = []    # List of citadel dicts, e.g. {"pos": (x, y), "owner": player}
land_tiles_remaining = 10
placing_land = True
game_message = "Place land tiles."
placed_pieces = {}   # {(x, y): {"type": piece, "owner": player}}
selected_piece = None
move_highlight_tiles = []      # Valid move tiles (for moving pieces)
capture_highlight_tiles = []   # Capture move tiles
current_player = 1
choice_highlight_tiles = []


# Center a 3x3 grid initially
grid_center_x = WIDTH // 2 // TILE_SIZE
grid_center_y = (HEIGHT - 100) // 2 // TILE_SIZE
min_x, max_x = grid_center_x - 1, grid_center_x + 1
min_y, max_y = grid_center_y - 1, grid_center_y + 1

# ------------------ Helper Functions ------------------
def handle_mounted_turtle_selection(x, y):

    piece = placed_pieces[(x, y)]
    mount = piece.get("mounted")
    if not mount:
        return (x, y)  # fallback if not mounted
    if piece["owner"] == mount["owner"]:
        decision = prompt_user_message("Press 'T' for Turtle or 'M' for Mounted:")
        if decision == "T":
            return {"pos": (x, y), "piece": piece, "move_mode": "turtle_no_capture"}
        elif decision == "M":
            return {"pos": (x, y), "piece": piece, "move_mode": "mounted_normal"}
    elif piece["owner"] == current_player and mount["owner"] != current_player:
        return {"pos": (x, y), "piece": piece, "move_mode": "turtle_enemy_mount"}
    elif piece["owner"] != current_player and mount["owner"] == current_player:
        if mount["type"] == "Rabbit":
            return {"pos": (x, y), "piece": piece, "move_mode": "mounted_rabbit"}
        else:
            return {"pos": (x, y), "piece": piece, "move_mode": "mounted_capture"}
    else:
        return (x, y)

def prompt_user_message(message):
    """
    Display a modal prompt on the screen and wait for the user to press a key.
    Press 'T' for Turtle or 'M' for Mounted.
    """
    prompt_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 100)
    pygame.draw.rect(screen, (0, 0, 0), prompt_rect)
    pygame.draw.rect(screen, (255, 255, 255), prompt_rect, 2)
    text_surface = FONT.render(message, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=prompt_rect.center)
    screen.blit(text_surface, text_rect)
    pygame.display.flip()
    
    waiting = True
    decision = None
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    decision = "T"
                    waiting = False
                elif event.key == pygame.K_m:
                    decision = "M"
                    waiting = False
    return decision


def prompt_turtle_choice(message):
    """
    Display a prompt asking the player to choose between using the Turtle or the Mounted piece.
    Press 't' for Turtle or 'm' for Mounted.
    """
    prompt_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 100)
    pygame.draw.rect(screen, (0, 0, 0), prompt_rect)
    pygame.draw.rect(screen, (255, 255, 255), prompt_rect, 2)
    text_surface = FONT.render(message, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=prompt_rect.center)
    screen.blit(text_surface, text_rect)
    pygame.display.flip()
    
    waiting = True
    choice = None
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    choice = "turtle"
                    waiting = False
                elif event.key == pygame.K_m:
                    choice = "mounted"
                    waiting = False
    return choice


def prompt_user(message):
    """
    Display a modal prompt on the screen and wait for the user to press a key.
    Press 'C' for Capture or 'M' for Mount.
    """
    # Define a prompt rectangle centered on the screen.
    prompt_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 100)
    # Draw a dark background for the prompt.
    pygame.draw.rect(screen, (0, 0, 0), prompt_rect)
    pygame.draw.rect(screen, (255, 255, 255), prompt_rect, 2)
    # Render the prompt message.
    text_surface = FONT.render(message, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=prompt_rect.center)
    screen.blit(text_surface, text_rect)
    pygame.display.flip()
    
    waiting = True
    decision = None
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    decision = "Capture"
                    waiting = False
                elif event.key == pygame.K_m:
                    decision = "Mount"
                    waiting = False
    return decision



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

def place_land_tile(x, y):
    global land_tiles_remaining, placing_land, game_message
    if (x, y) in board:
        return
    if not board or is_adjacent(x, y):
        board[(x, y)] = "L"
        land_tiles_remaining -= 1
        expand_board(x, y)
        if land_tiles_remaining == 0:
            placing_land = False
            game_message = "All land tiles placed! Click to place Citadels."
    else:
        game_message = "Invalid placement! Land must touch existing land."

def place_citadel(x, y):
    global game_message, piece_selection_done, current_player
    if (x, y) not in board or any(citadel["pos"] == (x, y) for citadel in citadels):
        return
    if len(citadels) == 0:
        citadels.append({"pos": (x, y), "owner": current_player})
        game_message = "First Citadel placed! Place the second Citadel."
        switch_player()  # Switch so second citadel belongs to other player.
    elif len(citadels) == 1:
        if is_adjacent(x, y):  # Basic connectivity check.
            citadels.append({"pos": (x, y), "owner": current_player})
            game_message = "Both Citadels placed! Confirm board layout."
            # Call confirmation function before moving to piece selection:
            confirm_board_layout()
            piece_selection_phase()
            piece_selection_done = True
            start_game_phase()
        else:
            game_message = "Invalid placement! Second Citadel must be adjacent."

def is_valid_piece_placement(x, y, player, piece_type):
    # For non-Turtle pieces, the tile must be land.
    # Allow placement if the tile is unoccupied or if it is occupied by a Turtle.
    if piece_type != "Turtle":
        if (x, y) not in board:
            return False
        # Allow placement if a Turtle is already there (even if it belongs to the enemy);
        # otherwise (if something else is there) it is invalid.
        if (x, y) in placed_pieces and placed_pieces[(x, y)]["type"] != "Turtle":
            return False
    else:
        # For Turtle pieces, only allow placement on water (no land tile) and ensure the square is unoccupied.
        if (x, y) in placed_pieces or (x, y) in board:
            return False

    # The tile must be adjacent to at least one citadel owned by the current player.
    adjacent_to_player = False
    for citadel in citadels:
        if citadel["owner"] == player:
            cx, cy = citadel["pos"]
            if abs(x - cx) <= 1 and abs(y - cy) <= 1:
                adjacent_to_player = True
                break
    if not adjacent_to_player:
        return False

    # Additionally, the tile must NOT be adjacent to any opponent citadel.
    for citadel in citadels:
        if citadel["owner"] != player:
            cx, cy = citadel["pos"]
            if abs(x - cx) <= 1 and abs(y - cy) <= 1:
                return False

    return True



# ------------------ Drawing Functions ------------------

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
    for (x, y) in move_highlight_tiles:
        pygame.draw.rect(screen, PLAYER1_COLOR if current_player == 1 else PLAYER2_COLOR, 
                         ((x - grid_min_x) * TILE_SIZE + offset_x,
                          (y - grid_min_y) * TILE_SIZE + offset_y,
                          TILE_SIZE, TILE_SIZE))
    for (x, y) in capture_highlight_tiles:
        pygame.draw.rect(screen, HIGHLIGHT_CAPTURE_COLOR, 
                         ((x - grid_min_x) * TILE_SIZE + offset_x,
                          (y - grid_min_y) * TILE_SIZE + offset_y,
                          TILE_SIZE, TILE_SIZE))
    for (x, y) in choice_highlight_tiles:
        pygame.draw.rect(screen, (0, 255, 255),  
                         ((x - grid_min_x) * TILE_SIZE + offset_x,
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


def draw_ui():
    if not piece_selection_done:
        ui_background = pygame.Rect(0, HEIGHT - UI_HEIGHT, WIDTH, UI_HEIGHT)
        pygame.draw.rect(screen, (50, 50, 50), ui_background)
        tile_text = f"Land Tiles Remaining: {land_tiles_remaining}" if placing_land else "Placing Citadels"
        tile_surface = FONT.render(tile_text, True, TEXT_COLOR)
        screen.blit(tile_surface, (20, HEIGHT - UI_HEIGHT + 20))
        msg_surface = FONT.render(game_message, True, TEXT_COLOR)
        screen.blit(msg_surface, (20, HEIGHT - UI_HEIGHT + 50))

def draw_selection_screen():
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
    
    # Draw offered pieces.
    for item in offered_pieces:
        pygame.draw.rect(screen, (100, 100, 200), item["rect"])
        piece_text = FONT.render(item["piece"], True, (255, 255, 255))
        screen.blit(piece_text, (item["rect"].x + 10, item["rect"].y + 10))
    
    # Draw stashes.
    for i, piece in enumerate(personal_stash):
        rect = pygame.Rect(personal_area.x + 10, personal_area.y + 50 + i * 60, 150, 50)
        pygame.draw.rect(screen, (120, 120, 220), rect)
        text_surface = FONT.render(piece, True, (255, 255, 255))
        screen.blit(text_surface, text_surface.get_rect(center=rect.center))
    for i, piece in enumerate(community_stash):
        rect = pygame.Rect(community_area.x + 10, community_area.y + 50 + i * 60, 150, 50)
        pygame.draw.rect(screen, (120, 120, 220), rect)
        text_surface = FONT.render(piece, True, (255, 255, 255))
        screen.blit(text_surface, text_surface.get_rect(center=rect.center))
    
    # If dragging a piece, draw it.
    if dragging_piece:
        pygame.draw.rect(screen, (200, 100, 100), dragging_piece["rect"])
        drag_text = FONT.render(dragging_piece["piece"], True, (255, 255, 255))
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
        text = FONT.render(piece, True, (200, 200, 200))
        screen.blit(text, (10, y_offset))
        y_offset += 30

def draw_personal_stash_ui():
    pygame.draw.rect(screen, (70, 70, 70), personal_stash_area)
    if personal_stash:
        # Divide the available width evenly by the number of pieces.
        piece_width = personal_stash_area.width / len(personal_stash)
        for i, piece in enumerate(personal_stash):
            # Calculate the center x–coordinate for each piece.
            piece_x = personal_stash_area.x + i * piece_width + piece_width/2
            text = FONT.render(piece, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(piece_x, personal_stash_area.centery))
            screen.blit(text, text_rect)
            # Optional: draw a debug rectangle for the clickable area.
            pygame.draw.rect(screen, (0,255,0), 
                             (personal_stash_area.x + i * piece_width, personal_stash_area.y, piece_width, personal_stash_area.height), 1)
    else:
        stash_text = "Personal Pool: (empty)"
        text_surface = FONT.render(stash_text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(midleft=(personal_stash_area.x + 10, personal_stash_area.centery))
        screen.blit(text_surface, text_rect)




def draw_community_stash_ui():
    global toggle_button_rect
    pygame.draw.rect(screen, (50, 50, 50), community_stash_area)
    
    # Upper section: turn indicator and toggle button.
    turn_text = FONT.render(f"Player {current_player}'s Turn", True, TEXT_COLOR)
    turn_rect = turn_text.get_rect(center=(community_stash_area.centerx, 20))
    screen.blit(turn_text, turn_rect)
    
    toggle_button_width = 100
    toggle_button_height = 40
    toggle_button_x = community_stash_area.centerx - toggle_button_width // 2
    toggle_button_y = turn_rect.bottom + 15  # increased spacing below turn indicator
    toggle_button_rect = pygame.Rect(toggle_button_x, toggle_button_y, toggle_button_width, toggle_button_height)
    pygame.draw.rect(screen, (255, 0, 0), toggle_button_rect, 4)
    toggle_text = FONT.render("Toggle", True, TEXT_COLOR)
    screen.blit(toggle_text, toggle_text.get_rect(center=toggle_button_rect.center))
    
    # Increase spacing before the separator line.
    separator_y = toggle_button_rect.bottom + 20  # extra space added here
    pygame.draw.line(screen, GRID_COLOR, (community_stash_area.x, separator_y), 
                     (community_stash_area.x + community_stash_area.width, separator_y), 2)
    
    # Lower section: Community Pool label on two lines.
    community_label = FONT.render("Community", True, TEXT_COLOR)
    pool_font = pygame.font.Font(None, 30)
    pool_font.set_underline(True)
    pool_label = pool_font.render("Pool", True, TEXT_COLOR)
    # Add extra space below the separator before the labels.
    community_label_rect = community_label.get_rect(center=(community_stash_area.centerx, separator_y + 30))
    pool_label_rect = pool_label.get_rect(center=(community_stash_area.centerx, community_label_rect.bottom + 20))
    screen.blit(community_label, community_label_rect)
    screen.blit(pool_label, pool_label_rect)
    
    # Draw community stash pieces below the pool label, centered.
    y_offset = pool_label_rect.bottom + 20
    global community_stash_base_y
    community_stash_base_y = y_offset  # Store the starting y–coordinate.
    for piece in community_stash:
        text = FONT.render(piece, True, TEXT_COLOR)
        # Center the text vertically in a 30-pixel high slot.
        text_rect = text.get_rect(center=(community_stash_area.centerx, y_offset + 15))
        screen.blit(text, text_rect)
        y_offset += 30




def highlight_valid_tiles(for_movement=False):
    global move_highlight_tiles, capture_highlight_tiles, choice_highlight_tiles
    move_highlight_tiles = []
    capture_highlight_tiles = []
    choice_highlight_tiles = []
    
    if not selected_piece:
        return

    # If selected_piece is a string, it's coming from the stash (placement phase)
    if isinstance(selected_piece, str):
        neighbors = lambda pos: [(pos[0] + dx, pos[1] + dy)
                                 for dx in [-1, 0, 1] for dy in [-1, 0, 1]
                                 if not (dx == 0 and dy == 0)]
        my_adjacent = set()
        for citadel in citadels:
            if citadel["owner"] == current_player:
                my_adjacent.update(neighbors(citadel["pos"]))
        if selected_piece == "Turtle":
            # For turtle placements, we only allow placement on water.
            move_highlight_tiles = [(x, y) for (x, y) in my_adjacent
                                    if (x, y) not in board and (x, y) not in placed_pieces]
        else:
            # For non-turtle pieces, allow moves onto land that is either empty or contains an unmounted turtle.
            move_highlight_tiles = [(x, y) for (x, y) in my_adjacent
                                    if (x, y) in board and (
                                        (x, y) not in placed_pieces or 
                                        (x, y) in placed_pieces and 
                                        placed_pieces[(x, y)]["type"] == "Turtle" and "mounted" not in placed_pieces[(x, y)]
                                    )]
        return

    # For movement phase, selected_piece is a tuple (board position) or a dict (for mounted turtles).
    if for_movement:
        if isinstance(selected_piece, dict):
            pos = selected_piece["pos"]
            piece_data = selected_piece["piece"]
            move_mode = selected_piece["move_mode"]
        else:
            pos = selected_piece
            piece_data = placed_pieces.get(pos, {})
            move_mode = None

        x, y = pos
        # When in a mounted move mode (including "mounted_normal"),
        # use the mount's type to determine valid moves.
        if move_mode in ["mounted_normal", "mounted_rabbit", "mounted_capture"]:
            moving_type = piece_data["mounted"]["type"]
        else:
            moving_type = piece_data["type"]

        potential_moves = get_valid_moves(moving_type, pos)

        for move in potential_moves:
            dx = move[0] - x
            dy = move[1] - y

            # Case: if the move mode is "turtle" (using the turtle itself with no capture),
            # only allow moving onto water.
            if move_mode == "turtle":
                if move in board and move not in placed_pieces:
                    move_highlight_tiles.append(move)
                continue

            # Case: moving as the mounted piece.
            elif move_mode in ["mounted", "mounted_rabbit"]:
                if move in board:
                    if move not in placed_pieces:
                        move_highlight_tiles.append(move)
                    elif placed_pieces[move]["owner"] != current_player:
                        capture_highlight_tiles.append(move)
            
            # Case: friendly turtle carrying an enemy mount.
            elif move_mode == "turtle_enemy_mount":
                if move in board:
                    if move not in placed_pieces:
                        move_highlight_tiles.append(move)
                    else:
                        target = placed_pieces[move]
                        if target["type"] == "Turtle" and "mounted" in target:
                            if target["mounted"]["owner"] != current_player:
                                capture_highlight_tiles.append(move)
            
            # Case: enemy turtle with your mounted piece that can capture both.
            elif move_mode == "mounted_capture":
                if move in board:
                    if move not in placed_pieces:
                        move_highlight_tiles.append(move)
                    else:
                        target = placed_pieces[move]
                        if target["type"] == "Turtle" and "mounted" in target:
                            capture_highlight_tiles.append(move)
                        elif target["owner"] != current_player:
                            capture_highlight_tiles.append(move)
            
            else:
                # Default behavior for unmounted pieces.
                if moving_type == "Turtle":
                    # Modified branch: allow moving onto any turtle square (friendly or enemy) that has no mount.
                    if move in placed_pieces and placed_pieces[move]["type"] == "Turtle" and "mounted" not in placed_pieces[move]:
                        move_highlight_tiles.append(move)
                    # Also allow water moves.
                    elif move not in placed_pieces and move not in board:
                        move_highlight_tiles.append(move)
                    # Otherwise, if adjacent to an enemy piece, allow capture.
                    elif max(abs(dx), abs(dy)) == 1 and move in placed_pieces and placed_pieces[move]["owner"] != piece_data["owner"]:
                        capture_highlight_tiles.append(move)
                else:
                    if move in board:
                        # If destination is empty or contains an unmounted turtle, allow mounting.
                        if (move not in placed_pieces) or (move in placed_pieces and 
                           placed_pieces[move]["type"] == "Turtle" and "mounted" not in placed_pieces[move]):
                            move_highlight_tiles.append(move)
                        elif placed_pieces[move]["owner"] != piece_data["owner"]:
                            capture_highlight_tiles.append(move)
                    else:
                        if (move in placed_pieces and 
                            placed_pieces[move]["type"] == "Turtle" and 
                            "mounted" not in placed_pieces[move]):
                            # Prioritize mounting even if the turtle is enemy.
                            move_highlight_tiles.append(move)
                        elif (move in placed_pieces and placed_pieces[move]["owner"] != piece_data["owner"]):
                            capture_highlight_tiles.append(move)
        return
    else:
        # Not in movement mode; simply highlight tiles adjacent to the player's citadels.
        neighbors = lambda pos: [(pos[0] + dx, pos[1] + dy)
                                 for dx in [-1, 0, 1] for dy in [-1, 0, 1]
                                 if not (dx == 0 and dy == 0)]
        my_adjacent = set()
        for citadel in citadels:
            if citadel["owner"] == current_player:
                my_adjacent.update(neighbors(citadel["pos"]))
        if isinstance(selected_piece, dict):
            piece_data = selected_piece["piece"]
        else:
            piece_data = placed_pieces.get(selected_piece, {})
        if piece_data.get("type") == "Turtle":
            move_highlight_tiles = [(x, y) for (x, y) in my_adjacent
                                    if (x, y) not in board and (x, y) not in placed_pieces]
        else:
            move_highlight_tiles = [(x, y) for (x, y) in my_adjacent
                                    if (x, y) in board and (
                                        (x, y) not in placed_pieces or 
                                        (x, y) in placed_pieces and placed_pieces[(x, y)]["type"] == "Turtle" and "mounted" not in placed_pieces[(x, y)]
                                    )]



def confirm_board_layout():
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




def move_piece(x, y):
    global selected_piece, graveyard
    move_executed = False

    # Only proceed if the clicked square is among the highlighted moves,
    # captures, or ambiguous choice moves.
    if not selected_piece or not ((x, y) in move_highlight_tiles or 
                                   (x, y) in capture_highlight_tiles or 
                                   (x, y) in choice_highlight_tiles):
        return

    if isinstance(selected_piece, dict):
        pos = selected_piece["pos"]
        mode = selected_piece["move_mode"]
        if mode == "mounted_normal":
            if pos not in placed_pieces:
                placed_pieces[pos] = selected_piece["piece"]
            turtle_piece = placed_pieces[pos]
            if "mounted" in turtle_piece:
                mounted_piece = turtle_piece["mounted"]
                # Temporarily remove the mount from the turtle.
                del turtle_piece["mounted"]
                if (x, y) in placed_pieces:
                    target = placed_pieces.get((x, y))
                    # If target is an enemy turtle:
                    if target["type"] == "Turtle" and target["owner"] != current_player:
                        # NEW: If the enemy turtle already carries a mount, automatically capture it.
                        if "mounted" in target:
                            graveyard.append(target["mounted"]["type"])
                            del target["mounted"]
                            target["mounted"] = mounted_piece
                            move_executed = True
                        else:
                            # Otherwise, prompt the user.
                            decision = prompt_user("Press 'C' for Capture or 'M' for Mount:")
                            if decision == "Capture":
                                del placed_pieces[(x, y)]
                                graveyard.append(target["type"])
                                turtle_piece["mounted"] = mounted_piece  # Reattach mount so it stays at pos.
                                placed_pieces[pos] = turtle_piece
                                move_executed = True
                            elif decision == "Mount":
                                del placed_pieces[(x, y)]
                                graveyard.append(target["type"])
                                placed_pieces[(x, y)] = mounted_piece
                                move_executed = True
                            else:
                                turtle_piece["mounted"] = mounted_piece
                                placed_pieces[pos] = turtle_piece
                    # If the target is an enemy piece of any other type, capture it normally.
                    elif target["owner"] != current_player:
                        del placed_pieces[(x, y)]
                        graveyard.append(target["type"])
                        placed_pieces[(x, y)] = mounted_piece
                        move_executed = True
                    elif (x, y) in move_highlight_tiles:
                        placed_pieces[(x, y)] = mounted_piece
                        move_executed = True
                    else:
                        turtle_piece["mounted"] = mounted_piece
                        placed_pieces[pos] = turtle_piece
                elif (x, y) in move_highlight_tiles:
                    placed_pieces[(x, y)] = mounted_piece
                    move_executed = True
                else:
                    turtle_piece["mounted"] = mounted_piece
                    placed_pieces[pos] = turtle_piece

        else:
            # For other move modes for mounted pieces.
            turtle_piece = placed_pieces.pop(pos)
            if mode == "turtle_no_capture":
                if (x, y) in move_highlight_tiles:
                    placed_pieces[(x, y)] = turtle_piece
                    move_executed = True
                else:
                    placed_pieces[pos] = turtle_piece

            elif mode == "turtle_enemy_mount":
                if (x, y) == pos:
                    if "mounted" in turtle_piece:
                        enemy_mount = turtle_piece.pop("mounted")
                        graveyard.append(enemy_mount["type"])
                        placed_pieces[pos] = turtle_piece
                        move_executed = True
                    else:
                        placed_pieces[pos] = turtle_piece
                elif (x, y) in move_highlight_tiles:
                    placed_pieces[(x, y)] = turtle_piece
                    move_executed = True
                else:
                    placed_pieces[pos] = turtle_piece

            elif mode == "mounted_rabbit":
                if "mounted" in turtle_piece:
                    rabbit_piece = turtle_piece.pop("mounted")
                    if (x, y) in capture_highlight_tiles:
                        target = placed_pieces.get((x, y))
                        if target and target["owner"] != current_player:
                            del placed_pieces[(x, y)]
                            graveyard.append(target["type"])
                            placed_pieces[(x, y)] = rabbit_piece
                            move_executed = True
                        else:
                            turtle_piece["mounted"] = rabbit_piece
                            placed_pieces[pos] = turtle_piece
                    elif (x, y) in move_highlight_tiles:
                        placed_pieces[(x, y)] = rabbit_piece
                        move_executed = True
                    else:
                        turtle_piece["mounted"] = rabbit_piece
                        placed_pieces[pos] = turtle_piece
                else:
                    placed_pieces[pos] = turtle_piece

            elif mode == "mounted_capture":
                if (x, y) == pos:
                    graveyard.append(turtle_piece["type"])
                    if "mounted" in turtle_piece:
                        graveyard.append(turtle_piece["mounted"]["type"])
                    move_executed = True
                elif (x, y) in capture_highlight_tiles:
                    if "mounted" in turtle_piece:
                        mount_piece = turtle_piece.pop("mounted")
                        target = placed_pieces.get((x, y))
                        if target and target["owner"] != current_player:
                            del placed_pieces[(x, y)]
                            graveyard.append(target["type"])
                            placed_pieces[(x, y)] = mount_piece
                            move_executed = True
                        else:
                            turtle_piece["mounted"] = mount_piece
                            placed_pieces[pos] = turtle_piece
                    else:
                        placed_pieces[pos] = turtle_piece
                elif (x, y) in move_highlight_tiles:
                    if "mounted" in turtle_piece:
                        mount_piece = turtle_piece.pop("mounted")
                        placed_pieces[(x, y)] = mount_piece
                        move_executed = True
                    else:
                        placed_pieces[pos] = turtle_piece
                else:
                    placed_pieces[pos] = turtle_piece

            else:
                placed_pieces[pos] = turtle_piece
    else:
        # Unmounted piece branch.
        moving_piece = placed_pieces.pop(selected_piece)
        if moving_piece["type"] == "Turtle":
            if (x, y) in move_highlight_tiles:
                placed_pieces[(x, y)] = moving_piece
                move_executed = True
            elif (x, y) in capture_highlight_tiles:
                target_piece = placed_pieces.get((x, y))
                if target_piece and target_piece["owner"] != moving_piece["owner"]:
                    del placed_pieces[(x, y)]
                    graveyard.append(target_piece["type"])
                    placed_pieces[selected_piece] = moving_piece
                    move_executed = True
                else:
                    placed_pieces[selected_piece] = moving_piece
            else:
                placed_pieces[selected_piece] = moving_piece
        else:
            if (x, y) in capture_highlight_tiles:
                target_piece = placed_pieces.get((x, y))
                if target_piece and target_piece["owner"] != moving_piece["owner"]:
                    if target_piece["type"] == "Turtle":
                        if "mounted" in target_piece:
                            graveyard.append(target_piece["mounted"]["type"])
                            del target_piece["mounted"]
                            target_piece["mounted"] = moving_piece
                            move_executed = True
                        else:
                            del placed_pieces[(x, y)]
                            graveyard.append(target_piece["type"])
                            placed_pieces[selected_piece] = moving_piece
                            move_executed = True
                    else:
                        del placed_pieces[(x, y)]
                        graveyard.append(target_piece["type"])
                        placed_pieces[(x, y)] = moving_piece
                        move_executed = True
                else:
                    placed_pieces[selected_piece] = moving_piece
            elif (x, y) in move_highlight_tiles:
                if (x, y) in placed_pieces and placed_pieces[(x, y)]["type"] == "Turtle" and "mounted" not in placed_pieces[(x, y)]:
                    placed_pieces[(x, y)]["mounted"] = moving_piece
                    move_executed = True
                else:
                    placed_pieces[(x, y)] = moving_piece
                    move_executed = True
            else:
                placed_pieces[selected_piece] = moving_piece

    if move_executed:
        selected_piece = None
        move_highlight_tiles.clear()
        capture_highlight_tiles.clear()
        choice_highlight_tiles.clear()
        switch_player()  # Toggle turn after a successful move.
    else:
        selected_piece = None
        move_highlight_tiles.clear()
        capture_highlight_tiles.clear()
        choice_highlight_tiles.clear()




def get_valid_moves(piece_type, pos):
    x, y = pos
    valid_moves = []
    if piece_type == "Bird":
        # Bird moves in straight lines horizontally or vertically.
        # It moves over contiguous land until water is encountered.
        # When water is encountered, include the square if it is occupied by a turtle.
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            step = 1
            while True:
                new_x = x + dx * step
                new_y = y + dy * step
                candidate = (new_x, new_y)
                if candidate in board:
                    valid_moves.append(candidate)
                    step += 1
                else:
                    # Candidate is water.
                    if candidate in placed_pieces and placed_pieces[candidate]["type"] == "Turtle":
                        valid_moves.append(candidate)
                    break

    elif piece_type == "Knight":
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                valid_moves.append((x + dx, y + dy))
    elif piece_type == "Turtle":
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                valid_moves.append((x + dx, y + dy))
    elif piece_type == "Rabbit":
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            valid_moves.append((x + dx, y + dy))
        for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
            valid_moves.append((x + dx, y + dy))
    elif piece_type in ["Builder", "Bomber", "Necromancer", "Assassin"]:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            valid_moves.append((x + dx, y + dy))
    return valid_moves



# ------------------ Mouse Click Handler ------------------
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

    # Stash selection: Check stash areas first.
    if not piece_selection_done:
        if personal_area.collidepoint(x, y):
            index = (y - personal_area.y - 50) // 60  # Adjust as needed.
            if 0 <= index < len(personal_stash):
                selected_piece = personal_stash[index]
                highlight_valid_tiles()
            return
        elif community_area.collidepoint(x, y):
            index = (y - community_area.y - 50) // 60  # Adjust as needed.
            if 0 <= index < len(community_stash):
                selected_piece = community_stash[index]
                highlight_valid_tiles()
            return
    else:
        # In game phase, use updated stash UI areas.
        if personal_stash_area.collidepoint(x, y):
            if personal_stash:
                piece_width = personal_stash_area.width / len(personal_stash)
                relative_x = x - personal_stash_area.x
                index = int(relative_x // piece_width)
                index = min(index, len(personal_stash) - 1)
                selected_piece = personal_stash[index]
                highlight_valid_tiles()
            return
        elif community_stash_area.collidepoint(x, y):
            index = int((y - community_stash_base_y) // 30)
            if 0 <= index < len(community_stash):
                selected_piece = community_stash[index]
                highlight_valid_tiles()
            return

    # Movement/Capture branch: if a piece is already selected for moving.
    # Modified to accept selected_piece as either a tuple or a dict.
    if isinstance(selected_piece, (tuple, dict)):
        if ((grid_x, grid_y) in move_highlight_tiles or 
            (grid_x, grid_y) in capture_highlight_tiles or 
            (grid_x, grid_y) in choice_highlight_tiles):
            move_piece(grid_x, grid_y)
            return

    # Board piece selection: if no stash selection was made, allow selection of a board piece.
    if (grid_x, grid_y) in placed_pieces:
        piece_data = placed_pieces[(grid_x, grid_y)]
        if piece_data["owner"] == current_player:
            # NEW: If the piece is a Turtle with a mounted piece, call our mounted-selection helper.
            if piece_data["type"] == "Turtle" and "mounted" in piece_data:
                selected_piece = handle_mounted_turtle_selection(grid_x, grid_y)
                # Immediately update valid move highlights based on the selected mode.
                highlight_valid_tiles(for_movement=True)
            else:
                selected_piece = (grid_x, grid_y)
                highlight_valid_tiles(for_movement=True)
        return

    # Placing a piece from a stash.
    if isinstance(selected_piece, str):
        if is_valid_piece_placement(grid_x, grid_y, current_player, selected_piece):
            print(f"Valid placement: {selected_piece} at ({grid_x}, {grid_y})")
            placed_pieces[(grid_x, grid_y)] = {"type": selected_piece, "owner": current_player}
            if selected_piece in personal_stash:
                personal_stash.remove(selected_piece)
            elif selected_piece in community_stash:
                community_stash.remove(selected_piece)
            selected_piece = None
            move_highlight_tiles.clear()
            capture_highlight_tiles.clear()
            choice_highlight_tiles.clear()
            switch_player()  # End turn after placement.
        else:
            print(f"Invalid placement at ({grid_x}, {grid_y}). It must be unoccupied, adjacent to your citadel, and not adjacent to an opponent's citadel.")
        return


# ------------------ Phase Functions ------------------
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

# ------------------ Main Game Loop ------------------
# Run the configuration phase once.
configuration_phase()

# Now update any dependent variables:
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
