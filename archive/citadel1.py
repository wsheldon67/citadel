#region ----------------------------------------------------------------Initialization--------------------------------------------------------------------
import pygame

pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Citadel")
game_state = 'CONFIGURATION'  # Start in configuration phase

# endregion

#region  ---------------------------------------------------------------Global Variables------------------------------------------------
font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

#Game Variables
offset_x = 0
offset_y = 0

#Colors
WATER_COLOR = (50,141,220) # Blue
LAND_COLOR = (169, 134, 63) # Brown
CITADEL_COLOR = (151, 151, 151) # Grey
GRID_COLOR = (255, 255, 255) # White
TEXT_COLOR = (255, 255, 255) # White
HIGHLIGHT_MOVE_COLOR = (255, 255, 0)    # Yellow
HIGHLIGHT_CAPTURE_COLOR = (255, 0, 0)     # Red
PLAYER1_COLOR = (255, 165, 0)  # Orange
PLAYER2_COLOR = (128, 0, 128)  # Purple
PLAYER3_COLOR = (0, 128, 0)    # Green
PLAYER4_COLOR = (0, 0, 255)    # Blue

#Game States
CONFIGURATION = "CONFIGURATION"
LAND_PLACEMENT = "LAND_PLACEMENT"
CITADEL_PLACEMENT = "CITADEL_PLACEMENT"
PIECE_SELECTION = "PIECE_SELECTION"
GAMEPLAY = "GAMEPLAY"
END_GAME = "END_GAME"

# endregion

#region ----------------------------------------------------------------Helpers and Handlers------------------------------------------------

def handle_click(event):
    global game_state, config_prompt_defaults, NUM_PLAYERS, LAND_PER_PLAYER, NUM_LAND_PIECES, current_player

    if event.type == pygame.MOUSEBUTTONDOWN:  # Ensure it's a MOUSEBUTTONDOWN event
        mouse_x, mouse_y = pygame.mouse.get_pos()  # Use pygame.mouse.get_pos() instead of event.pos
        
        if game_state == 'CONFIGURATION':
            for key, (dec_button, inc_button) in buttons_dict.items():
                if dec_button.collidepoint((mouse_x, mouse_y)):
                    config_prompt_defaults[key] = max(1, config_prompt_defaults[key] - 1)
                elif inc_button.collidepoint((mouse_x, mouse_y)):
                    config_prompt_defaults[key] += 1            
            # Check if the Continue button was clicked
            if continue_button_rect.collidepoint((mouse_x, mouse_y)):
                # Transfer the data from config_prompt_defaults to actual game variables
                NUM_PLAYERS = config_prompt_defaults["Number of Players"]
                LAND_PER_PLAYER = config_prompt_defaults["Land Pieces Per Player"]
                NUM_LAND_PIECES = NUM_PLAYERS * LAND_PER_PLAYER
                current_player = random.randint(1, NUM_PLAYERS)
                
                game_state = 'LAND_PLACEMENT'
        
        elif game_state == 'LAND_PLACEMENT':
            # Convert screen coordinates to grid coordinates using offset_x and offset_y
            grid_x = (mouse_x - offset_x) // TILE_SIZE
            grid_y = (mouse_y - offset_y) // TILE_SIZE
            
            # Adjust to account for the grid's shifting position
            land_tiles = [(x, y) for (x, y), tile_type in grid.items() if tile_type in ("LAND", "CITADEL")]
            
            if land_tiles:
                min_x = min(x for x, y in land_tiles) - 3
                min_y = min(y for x, y in land_tiles) - 3
            else:
                min_x = grid_center_x - 3
                min_y = grid_center_y - 3

            # Calculate the actual grid position
            actual_x = min_x + grid_x
            actual_y = min_y + grid_y

            place_land(actual_x, actual_y)

        elif game_state == 'CITADEL_PLACEMENT':
            global NUM_PLACED_CITADELS 

            grid_x = (mouse_x - offset_x) // TILE_SIZE
            grid_y = (mouse_y - offset_y) // TILE_SIZE

            if (grid_x, grid_y) in grid and grid[(grid_x, grid_y)] == "LAND":
                grid[(grid_x, grid_y)] = "CITADEL"
                NUM_PLACED_CITADELS += 1 

                current_player = (current_player % NUM_PLAYERS) + 1

                # Check if all citadels are placed
                if NUM_PLACED_CITADELS == NUM_PLAYERS:
                    game_state = 'PIECE_SELECTION'
                    show_popup_alert("Citadel Placement Complete. Moving to Piece Selection Phase.")

def show_popup_alert(message):
    # Define dimensions for the pop-up box
    box_width, box_height = 600, 200
    box_x = (WIDTH - box_width) // 2  # Center horizontally
    box_y = (HEIGHT - box_height) // 2  # Center vertically

    # Draw the pop-up box
    pygame.draw.rect(screen, (0, 0, 0), (box_x, box_y, box_width, box_height))  # Black background
    pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 3)  # White border

    # Render the message text
    font = pygame.freetype.SysFont('Arial', 24)
    text_surface, text_rect = font.render(message, (255, 255, 255))
    text_rect.center = (box_x + box_width // 2, box_y + box_height // 2)
    screen.blit(text_surface, text_rect)

    pygame.display.flip()
    pygame.time.wait(500)

#endregion

#region ----------------------------------------------------------------Configuration Phase---------------------------------------------------------------
# Configuration Variables
NUM_PLAYERS = 2
LAND_PER_PLAYER = 5
NUM_LAND_PIECES = LAND_PER_PLAYER * NUM_PLAYERS
PERSONAL_PER_PLAYER = 3
NUM_PERSONAL_PIECES = PERSONAL_PER_PLAYER * NUM_PLAYERS
COMMUNITY_PER_PLAYER = 3
NUM_COMMUNITY_PIECES = COMMUNITY_PER_PLAYER * NUM_PLAYERS

config_prompt_defaults = {
    "Number of Players": NUM_PLAYERS,
    "Land Pieces Per Player": LAND_PER_PLAYER,
    "Personal Pieces Per Player": PERSONAL_PER_PLAYER,
    "Community Pieces Per Player": COMMUNITY_PER_PLAYER
}

LINE_HEIGHT = 70
total_lines = len(config_prompt_defaults)
bottom_prompt_y = (HEIGHT - (total_lines * LINE_HEIGHT)) // 2 + total_lines * LINE_HEIGHT

#-------------------------------------------------------------------------------Configuration Defs---------------------------------------------------------------

def config_ui(screen, config_prompt_defaults):
    screen.fill((0, 0, 0))  # black background
    border_color = (128, 128, 128)  # grey border color
    pygame.draw.rect(screen, border_color, screen.get_rect(), 5)  # draw border with thickness 5

    buttons_dict = {}
    total_lines = len(config_prompt_defaults)
    total_height = total_lines * LINE_HEIGHT
    start_y = (HEIGHT - total_height) // 2  # Vertical centering

    prompts = [
        f"Number of Players (1-4): {config_prompt_defaults['Number of Players']}",
        f"Land Pieces Per Player: {config_prompt_defaults['Land Pieces Per Player']}",
        f"Personal Pieces Per Player: {config_prompt_defaults['Personal Pieces Per Player']}",
        f"Community Pieces Per Player: {config_prompt_defaults['Community Pieces Per Player']}"
    ]
    # Calculate maximum prompt width (if needed for alignment)
    max_width = 0
    for prompt in prompts:
        text_surface = font.render(prompt, True, (255, 255, 255))
        if text_surface.get_width() > max_width:
            max_width = text_surface.get_width()
    
    # Use a computed x_text if desired; here we'll center the text block horizontally.
    x_text = ((WIDTH - max_width + 80 + 5) // 2)
    
    for idx, (key, value) in enumerate(config_prompt_defaults.items()):
        y_offset = start_y + idx * LINE_HEIGHT

        prompt = f"{key}: {value}"
        text_surface = font.render(prompt, True, (255, 255, 255))
        screen.blit(text_surface, (x_text, y_offset))

        # Compute button positions: place buttons immediately to the left of the prompt.
        button_width, button_height = 40, 30
        x_buttons = x_text - button_width - 70  # adjust spacing as needed
        y_buttons = y_offset + (text_surface.get_height() - button_height) // 2

        # Create button rectangles
        dec_button = pygame.Rect(x_buttons, y_buttons, button_width, button_height)
        inc_button = pygame.Rect(x_buttons + button_width + 5, y_buttons, button_width, button_height)

        # Draw the buttons
        pygame.draw.rect(screen, (220, 20, 60), dec_button, 0, border_radius=5)   # Red: decrement
        pygame.draw.rect(screen, (107, 142, 35), inc_button, 0, border_radius=5)    # Green: increment

        # Render button text ("-" and "+")
        minus_text = font.render("-", True, (255, 255, 255))
        plus_text = font.render("+", True, (255, 255, 255))
        minus_rect = minus_text.get_rect(center=dec_button.center)
        plus_rect = plus_text.get_rect(center=inc_button.center)
        screen.blit(minus_text, minus_rect)
        screen.blit(plus_text, plus_rect)

        buttons_dict[key] = (dec_button, inc_button)

    return buttons_dict

def draw_continue_button(screen, bottom_prompt_y):
    button_text = "Continue to Board Creation"
    button_width, button_height = 500, 50  # Adjust dimensions as needed
    x = (WIDTH - button_width) // 2
    y = bottom_prompt_y + 20  # 100 pixels below the bottom prompt
    button_rect = pygame.Rect(x, y, button_width, button_height)
    pygame.draw.rect(screen, (200, 200, 200), button_rect, 0, border_radius=5)
    text_surface = font.render(button_text, True, (0, 0, 0))
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)
    return button_rect

#endregion

#region ----------------------------------------------------------------Board Creation Phase-----------------------------------

import pygame.freetype
import random
TILE_SIZE = 40
WIDTH, HEIGHT = 1000, 700  # Make sure these variables are defined globally
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

NUM_PLAYERS = 2
LAND_PER_PLAYER = 10
NUM_LAND_PIECES = LAND_PER_PLAYER * NUM_PLAYERS
NUM_PLACED_LANDS = 1  # Start with the central land tile already placed
NUM_PLACED_CITADELS = 0
current_player = random.randint(1, NUM_PLAYERS)

# Colors
WATER_COLOR = (50, 141, 220)  # Blue
LAND_COLOR = (169, 134, 63)  # Brown
CITADEL_COLOR = (151, 151, 151)  # Grey
GRID_COLOR = (255, 255, 255)  # White
TEXT_COLOR = (255, 255, 255)  # White

# Initialize Grid

grid_center_x = WIDTH // 2 // TILE_SIZE
grid_center_y = (HEIGHT - 100) // 2 // TILE_SIZE
grid = {}

for x in range(grid_center_x - 3, grid_center_x + 4):
    for y in range(grid_center_y - 3, grid_center_y + 4):
        if x == grid_center_x and y == grid_center_y:
            grid[(x, y)] = "LAND"
        else:
            grid[(x, y)] = "WATER"

def draw_grid():
    global offset_x, offset_y

    screen.fill((0, 0, 0))

    # Calculate bounds based on current land tiles
    land_tiles = [(x, y) for (x, y), tile_type in grid.items() if tile_type in ("LAND", "CITADEL")]
    if land_tiles:
        min_x = min(x for x, y in land_tiles) - 3
        max_x = max(x for x, y in land_tiles) + 3
        min_y = min(y for x, y in land_tiles) - 3
        max_y = max(y for x, y in land_tiles) + 3
    else:
        min_x, max_x = grid_center_x - 3, grid_center_x + 3
        min_y, max_y = grid_center_y - 3, grid_center_y + 3

    # Calculate grid size
    grid_width = (max_x - min_x + 1) * TILE_SIZE
    grid_height = (max_y - min_y + 1) * TILE_SIZE

    # Calculate offsets to keep the grid centered
    offset_x = (WIDTH - grid_width) // 2
    offset_y = (HEIGHT - grid_height) // 2

    # Draw the grid tiles
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            rect = pygame.Rect(offset_x + (x - min_x) * TILE_SIZE, 
                               offset_y + (y - min_y) * TILE_SIZE, 
                               TILE_SIZE, TILE_SIZE)
            
            if (x, y) in grid:
                tile_type = grid[(x, y)]
                if tile_type == "WATER":
                    pygame.draw.rect(screen, WATER_COLOR, rect)
                elif tile_type == "LAND":
                    pygame.draw.rect(screen, LAND_COLOR, rect)
                elif tile_type == "CITADEL":
                    pygame.draw.rect(screen, CITADEL_COLOR, rect)
            else:
                pygame.draw.rect(screen, WATER_COLOR, rect)
                
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)  # Draw grid lines

    pygame.display.flip()

def draw_remaining_land_message():
    message = f"Player {current_player}'s Turn. Remaining Land Pieces: {NUM_LAND_PIECES - NUM_PLACED_LANDS}"
    text_surface = font.render(message, True, TEXT_COLOR)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, 20))
    screen.blit(text_surface, text_rect)
    pygame.display.update(text_rect)

def place_land(x, y):
    global NUM_PLACED_LANDS, current_player, game_state

    if (x, y) not in grid or grid[(x, y)] == "WATER":
        # Ensure tile is adjacent to existing land
        adjacent_to_land = any((x + dx, y + dy) in grid and grid[(x + dx, y + dy)] == "LAND"
                               for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)])
        if adjacent_to_land:
            grid[(x, y)] = "LAND"
            NUM_PLACED_LANDS += 1
            current_player = (current_player % NUM_PLAYERS) + 1
            
            # Check if all land tiles have been placed
            if NUM_PLACED_LANDS >= NUM_LAND_PIECES:
                game_state = 'CITADEL_PLACEMENT'
                show_popup_alert("All land tiles placed. Moving to Citadel Placement.")
        else:
            show_popup_alert("Land tiles must be placed adjacent to existing land.")
    else:
        show_popup_alert("Invalid placement. Tile already occupied.")

def highlight_valid_citadel_placement():
    valid_tiles = []
    for (x, y), tile_type in grid.items():
        if tile_type == "LAND":
            if NUM_PLACED_CITADELS == 0:
                valid_tiles.append((x, y))  # First citadel can be placed on any land tile
            else:
                # Check if the tile is connected orthogonally to an existing citadel
                orthogonal_connections = [(x + dx, y + dy) for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]]
                connected = any((nx, ny) in grid and grid[(nx, ny)] == "CITADEL" for nx, ny in orthogonal_connections)

                # Check distance of 2 tiles from all other citadels
                too_close = False
                for (cx, cy), c_type in grid.items():
                    if c_type == "CITADEL" and abs(cx - x) + abs(cy - y) <= 2:
                        too_close = True
                        break

                if connected and not too_close:
                    valid_tiles.append((x, y))
    
    # Highlight valid tiles (Adjusted for dynamic grid rendering)
    land_tiles = [(x, y) for (x, y), tile_type in grid.items() if tile_type in ("LAND", "CITADEL")]

    if land_tiles:
        min_x = min(x for x, y in land_tiles) - 3
        min_y = min(y for x, y in land_tiles) - 3
    else:
        min_x = grid_center_x - 3
        min_y = grid_center_y - 3

    # Render valid placement highlights properly aligned with the grid
    for x, y in valid_tiles:
        rect = pygame.Rect(
            offset_x + (x - min_x) * TILE_SIZE,
            offset_y + (y - min_y) * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE
        )
        pygame.draw.rect(screen, (0, 255, 0), rect, 3)  # Green outline to indicate valid placement



def place_citadel(x, y):
    global NUM_PLACED_CITADELS, current_player

    if (x, y) in grid and grid[(x, y)] == "LAND":
        valid_tiles = []
        highlight_valid_citadel_placement()

        if (x, y) in valid_tiles:
            grid[(x, y)] = "CITADEL"
            NUM_PLACED_CITADELS += 1 
            current_player = (current_player % NUM_PLAYERS) + 1
        else:
            show_popup_alert("Invalid Citadel placement. Try again.")
    else:
        show_popup_alert("Citadels can only be placed on land tiles.")


def show_citadel_confirmation_message():
    show_popup_alert("Confirm Citadel Placement? Yes / Replace")

def check_for_transition():
    global game_state
    if NUM_PLACED_LANDS >= NUM_LAND_PIECES:
        game_state = 'CITADEL_PLACEMENT'
    elif NUM_PLACED_CITADELS >= NUM_PLAYERS:
        game_state = 'PIECE_SELECTION'

#endregion

#region------------------------------------------------------------------Main game loop--------------------------------------------------------------------
running = True
buttons_dict = config_ui(screen, config_prompt_defaults)
total_lines = len(config_prompt_defaults)
bottom_prompt_y = (HEIGHT - (total_lines * LINE_HEIGHT)) // 2 + total_lines * LINE_HEIGHT
continue_button_rect = draw_continue_button(screen, bottom_prompt_y)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        handle_click(event)

    if game_state == 'CONFIGURATION':
        buttons_dict = config_ui(screen, config_prompt_defaults)
        continue_button_rect = draw_continue_button(screen, bottom_prompt_y)
    elif game_state == 'LAND_PLACEMENT':
        draw_grid()
        draw_remaining_land_message()

    elif game_state == 'CITADEL_PLACEMENT':
        draw_grid()  # Render the board
        highlight_valid_citadel_placement()  # Highlight valid citadel placement tiles
        draw_remaining_land_message()  # Show message if desired
        check_for_transition()  # Check if all citadels are placed

    pygame.display.flip()
    clock.tick(30)


pygame.quit()

#endregion
