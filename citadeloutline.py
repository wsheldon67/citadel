#----------------------------------------------------------------Initilization------------------------------------------------
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

#---------------------------------------------------------------Game Variables------------------------------------------------
#Configuration Variables
NUM_PLAYERS = 2
NUM_LAND_PIECES = 10*NUM_PLAYERS
NUM_PERSONAL_PIECES = 3*NUM_PLAYERS
NUM_COMMUNITY_PIECES = 3*NUM_PLAYERS

#Counter Variables
NUM_CITADELS = 1*NUM_PLAYERS
NUM_PLACED_CITADELS = 0
NUM_CITADELS_REMAINING = NUM_CITADELS - NUM_PLACED_CITADELS
NUM_PLACED_LANDS = 0
NUM_LAND_REMAINING = NUM_LAND_PIECES- NUM_PLACED_LANDS

#Helper Variables
IS_ORTHOGONALLY_CONNECTED = False
CURRENT_PLAYER = 1

#---------------------------------------------------------------Lists------------------------------------------------
AVAILABLE_PIECES = []
GRAVEYARD = []
PLACED_PIECES = []
PLAYER1_PIECES = []
PLAYER2_PIECES = []
PLAYER3_PIECES = []
PLAYER4_PIECES = []
COMMUNITY_PIECES = []

#---------------------------------------------------------------UI Variables------------------------------------------------
#-------------Configuration Phase UI Variables




#-------------Board Creation Phase UI Variables

#TODO:Center a 3x3 grid initially
grid_center_x = WIDTH // 2 // TILE_SIZE
grid_center_y = (HEIGHT - 100) // 2 // TILE_SIZE
min_x, max_x = grid_center_x - 1, grid_center_x + 1
min_y, max_y = grid_center_y - 1, grid_center_y + 1


#--------------Piece Selection Phase UI Variables TODO: REMOVAL_HEIGHT???
selection_personal_pool = pygame.Rect(0, 0, int(WIDTH * 0.25), HEIGHT - REMOVAL_HEIGHT)
selection_offered_pool = pygame.Rect(int(WIDTH * 0.25), 0, int(WIDTH * 0.5), HEIGHT - REMOVAL_HEIGHT)
selection_community_pool = pygame.Rect(int(WIDTH * 0.75), 0, int(WIDTH * 0.25), HEIGHT - REMOVAL_HEIGHT)
selection_removal_zone = pygame.Rect(0, HEIGHT - REMOVAL_HEIGHT, WIDTH, REMOVAL_HEIGHT)

#--------------Game Play Phase UI Variables
gameplay_personal_pool = pygame.Rect(150, HEIGHT - 75, WIDTH - 300, 75)
gameplay_community_pool = pygame.Rect(WIDTH - 150, 0, 150, HEIGHT)
graveyard_area = pygame.Rect(0, 0, 150, HEIGHT)
#TODO:gameplay_opponent_pool =
#TODO:gameplay_board =

#---------------End Game Phase UI Variables

#---------------Button UI Variables
standard_prompt_button = pygame.Rect(0, 0, WIDTH, HEIGHT - UI_HEIGHT)
standard_prompt_message = pygame.Rect(0, 0, WIDTH, HEIGHT - UI_HEIGHT)

#---------------------------------------------------------------Game Colors------------------------------------------------

WATER_COLOR = (50,141,220) # Blue
LAND_COLOR = (169, 134, 63) # Brown
CITADEL_COLOR = (151, 151, 151) # Grey
GRID_COLOR = (255, 255, 255) # White
TEXT_COLOR = (255, 255, 255) # White
HIGHLIGHT_MOVE_COLOR = (255, 255, 0)    # Yellow
HIGHLIGHT_CAPTURE_COLOR = (255, 0, 0)     # Red
PLAYER1_COLOR = (255, 165, 0)  # Orange
PLAYER2_COLOR = (128, 0, 128)  # Purple
PLAYER3_COLOR = (0, 128, 0)    # GreenTODO: Change to a different color
PLAYER4_COLOR = (0, 0, 255)    # Blue TODO: Change to a different color

#---------------------------------------------------------------Piece UI------------------------------------------------
TURTLE_UI = pygame.image.load("turtle.png")
KNIGHT_UI = pygame.image.load("knight.png")
BIRD_UI = pygame.image.load("bird.png")
BOMBER_UI = pygame.image.load("bomber.png")
ASSASSIN_UI = pygame.image.load("assassin.png")
BUILDER_UI = pygame.image.load("builder.png")
RABBIT_UI = pygame.image.load("rabbit.png")
NECROMANCER_UI = pygame.image.load("necromancer.png")
#---------------------------------------------------------------Helper Functions---------------------------------------
#grid helpers---------------------------------------------
def is_diagonal():

def is_orthogonal():

def citadel_is_connected():
    #the citadels must be connected at all times by an orthogonal series of lands and turtles
    #players may not take any actions that would break a connection, either by moving a land with a builder or moving a turtle that contributes to the sole connection of citadels

#turtle helpers-----------------------------------------------
def is_mounted():
       #a piece shares a water tile with a turtle

def friendlyT_friendlyP():
    #the Turtle should be able to move as normal turtle rules dictate, but should not be allowed to capture

def friendlyT_unfriendlyP():
    #the turtle should be able to move as normal turtle rules dicatate, but should only be allowed to capture the piece it is sharing a tile with
def unfriendlyT_friendlyP():
    #the piece sharing the square with the turtle should be able to move as normal and capture as normal, but capturing the turtle should send both the turtle and the piece to the graveyard
       
#piece helpers--------------------------------------------------
def standard_piece_move():
    #can move orthogonally 1 tile to an adjacent land tile
    #can not move to a water tile
    #can not move to a tile that is already occupied by a player piece, unless that piece is a turtle
def standard_piece_capture():
    #can capture orthogonally 1 tile to an adjacent land tile
    #can not capture diagonally
    #can capture opponent pieces it shares a tile with

def standard_turtle_capture():
    #when capturing a turtle, 
        #if capturing from land
            #the turtle goes to the graveyard and the capturing piece stays in it's current location
        #if capturing while sharing with the turtle
            #turtle and piece both go to graveyard
       
def landing_turtle_capture():
    #when capturing a turtle, the piece moves to a landing tile that is the land tile closest to the turtle, and the turtle goes to the graveyard
    #if capturing while sharing a tile with the turtle
        #both turtle and piece go to the graveyard

#---------------------------------------------------------------Entities------------------------------------------------
def land():
def water():
def citadel():

#---------------------------------------------------------------Pieces-----------------------------------------------------------
#Turtle---------------------------------------------
def turtle_move():
        #can move orthogonally to an adjacent water tile, or diagonally to an adjacent water tile
        #can not move to a land tile
        #can not move to a tile that is already occupied by a player piece, including turtles

def turtle_capture():
        #when capture orthogonal pieces on land tile
            #send captured piece to graveyard to graveyard
            #stay in place
        #when capture piece it shares tile with
            #send captured piece to graveyard
            #stay in place
def turtle_turtle_capture():
    #a turtle captures another turtle by moving to the tile of the turtle being captured, and the turtle being captured goes to the graveyard

#Knight--------------------------------------------
def knight_move():
    #can move orthogonal or diagonal onto unoccupied
    #can only move on land tiles or turtle tiles
def knight_capture():
    #can capture pieces orthogonal or diagonal
def knight_turtle_capture():
    #standard turtle capture
#Bird------------------------------------------------------
def bird_move():
    #can move in a straight line in orthogonal directions until reaching a water tile or another piece
def bird_capture():
    #can capture the first enemy piece in a straight line
def bird_turtle_capture():
    #landing_turtle_capture
#Bomber-------------------------------------------------------
def bomber_move():
    #standard piece move
def bomber_capture():
    #standard piece capture
def bomber_ability():
    #capture itself and capture any piece or citadel that is adjacent to it
def bomber_turtle_capture():
    #standard turtle capture
#Assassin--------------------------------------------------------
def assassin_move():
    #standard move()
def assassin_capture():
    #identifies a piece upon placement
    #that is the only valid target
def assassin_ability():
    #can move an extra 1 space orthogonal
    #then moves through any number of adjacent pieces
    #then moves an extra 1 space orthogonal
    #can capture target
def assassin_turtle_capture():
    #standard turtle capture
#Builder------------------------------------------------------------
def builder_move():
    #standard move
def builder_capture():
    #no capture
def builder_ability():
    #highlight orthogonal land tiles
    #left click highlighted land tile
        #highlight valid land tile moves in yellow
            #valid land tile moves are empty water tiles orthogonal to the land tile
        #if highlighted location is left-clicked, land tile moves to new positon
            #any pieces on that water tile go to the graveyard
        #if the initial selected tile is selected again
            #the land tile is added to the land tile pile in the community pool UI
            #any pieces that were on the land tile go to the graveyard
    
#Rabbit----------------------------------------------------------------
def rabbit_move():
    #move either 1 or 2 orthogonal squares
def rabbit_capture():
    #capture from 2 orthogonal squares away
def rabbit_turtle_capture():
    #landing_turtle_capture
    
#Necromancer----------------------------------------------------------
def necromancer_move():
    #standard_piece_move
def necromancer_capture():
    #standard_piece_capture
def necromancer_ability():
    #TODO: might need original_necromancer_location or something similar
    #select a piece in the graveyard
    # remove the necromancer from its position and return it to it's original pool
    #place the graveyard piece on position the necromancer just vacated
def necromancer_turtle_capture():
    #standard_turtle_capture

#---------------------------------------------------------------Prompts & Messages------------------------------------------------

def land_remaining_message():
    #Land pieces remaining: num_land_remaining

def citadel_confirmation_message():
    #Confirm citadel placement: Yes button, replace button

def pool_full_message():
    #Pool full: You cannot add more pieces to your pool. Please remove a piece before adding another.

def piece_selection_confirmation_message():
    #Piece selection confirmation: Continue button

def end_game_message():
    #Player ____ Wins! Would you like to play again?  Yes, No buttons

#---------------------------------------------------------------Game Phases------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------Configuration Phase----------------------------------------
def configuration_phase():
    #user input set num_players = default 2 (between 1 and 4)
    #user input set num_land_pieces = default 10*num_players
    #user input set num_personal_pieces = default 3*num_players
    #user input set num_community_pieces = default 3*num_players

def configuration_phase_UI():
        #black screen grey border
        #white text
        #prompt for game variables with defaults pre-filled text box:
            # "Number of Players: (adjustable default)
            # "Land Pieces Per Player: (adjustable default)
            # "Personal Pieces Per Player: (adjustable default)
            # "Community Pieces Per Player: (adjustable default)
        
#---------------------------------------------------------------Board Creation Phase------------------------------------------------
def board_creation_phase():
    land_placement():
    citadel_placement():

def land_placement():
    #auto place a land in the center of the board, adjust num_placed_land +1
    # select random player for current_player
       #while num_land_remaining > 0
            #highlight_valid_land_placement()
                #land placement is valid if it is on an empty water tile that is adjacent to an existing land tile, highlight in color of current_player
            #register mouse click on valid land placement
            #place land on the tile
            #adjust placed_land +1
            #switch current_player
def citadel_placement():
       #while NUM_CITADELS_REMAINING  > 0
            #highlight_valid_citadel_placement options for citadel 1 in color of current_player
                # citadel placement is valid if it is on an empty land tile that is 2 tiles away from any other citadel.
            #register mouse click on valid citadel placement
            #place citadel on valid tile and assign to current_player
            #adjust num_placed_citadels +1
            #print citadel_confirmation_message()
                    #if replace, go back to highligh valid citadel placement options for citadel 1
                    #else
                        # switch current_player

def highlight_valid_land_placement():
    #highlight valid land placement options in color of current_player
        #land placement is valid if it is on an empty water tile that is adjacent to an existing land tile

def highlight_valid_citadel_placement():
    #highlight valid citadel placement options in color of current_player
        #the first citadel placement is valid if it is on an empty land tile
        #additional citadel placement is valid if it is placed in a location that is orthoganlly connected to the existing citadel(s) by land tiles, and more than 2 tiles away from the existing citadel.
        

def board_creation_phase_UI():
        #black box on bottom with grey border
            #white text
            #messages
                #while land placement: land pieces remaining
                #while citadel placement: 
                #citadels placed, continue?
        #white grid with grey border
            #land pieces are brown
            #water pieces are blue
            #citadel pieces are grey
            #grid only shows land +3 tiles from land pieces, and adjusts size accordingly

#---------------------------------------------------------------Piece Selection Phase------------------------------------------------
def piece_selection_phase():
    #players select pieces from available_pieces. They do this at the same time, but they can't see each other's selections
    #players can drag and drop to either the community or personal piece area
    #players can select a piece multiple times
    #players can drag a piece from the community or personal piece area back to available_pieces
    #the community and personal piece areas can only hold the number of pieces specified in the game variables
        #if the player reaches the maximum and tries to add another piece, pool_full_message is displayed
    #once the pools are full, piece_selection_confirmation_message is displayed
        #if the player chooses to replace a piece, they can drag and drop a piece from their pools to the available_pieces area
        #if the player chooses to keep their pieces, select continue to move to the game play phase
def piece_selection_phase_UI():
    #screen split into 3 vertical sections with grey borders
        #left section is for player1 pieces
            #white text
            #grey border
            #drag and drop pieces from available_pieces to this section
        #middle section is for available_pieces
            #white text
            #grey border
            #drag and drop pieces from this section to either left or right section
            #pieces are listed with their names and images
        #right section is for community pieces
            #white text
            #grey border
            #drag and drop pieces from available_pieces to this section
    
#---------------------------------------------------------------Game Play Phase------------------------------------------------
def game_play_phase():
    #chosen pieces are populated into piece selection areas
    #players take turns placing, moving, capturing, or using abilities of their pieces
    #after a move, capture, or ability is used, the game should:
        #check for win conditions
        #switch current_player
        #if a player has no valid moves, like placing, moving, capturing, or using abilities, they lose their turn and the next player goes.

def is_valid_piece_placement():
    #check valid placement options, and highlight them in color of current_player
        #valid placement options are:
            #if the piece is a non-turtle
                #placing a piece on an empty land tile that is adjacent to the players citadel
                #placing a piece on a turtle that is adjacent to a players citadel
            #if the piece is a turtle
                #placing a piece on an empty water tile that is adjacent to the players citadel
    
def piece_placement():
    #if current_player left-clicks from either their pool or the community pool
    # run is_valid_piece_placement()

    #register left-mouse click on highlight from is_valid_piece_placement()
        #place piece on the tile
        #add to placed_pieces list
        #add to current_player pieces list
        #switch current_player

def is_valid_capture():
    #check valid capture options, and highlight them in red
        #valid capture options are:
            #check entity piece capture rules

def piece_capture():
    #if current player left-clicks a piece that belongs in both placed_pieces and current_player pieces list
    #run is_valid_capture()
    #register mouse click on highlight from is_valid_capture()
        #capture piece and add to graveyard list
        #remove from any player_pieces list
        #switch current_player

def use_ability():
    #current player right-clicks a piece that belongs in both placed_pieces and current_player pieces list
    #check if the piece has an ability
        #if so, run the ability function for that piece
        #switch current_player

def is_valid_move():
    #check valid move options, and highlight them in yellow
    #valid move options are:
        #check entity piece move rules
        #check if the piece is moving to a tile that is already occupied by a player piece
       

def piece_move():
    #current player left-clicks a piece that belongs in both placed_pieces and current_player pieces list
    #run is_valid_move()
        #register mouse click on highlight from is_valid_move()
        #move piece to the tile
        #switch current_player


def win_condition_check():
    #check if any player has captured or moved into the opponent's citadel. If so, that player wins.


def game_play_phase_UI():
    #screen split into 5 sections
        #left section is for graveyard
        #right section is for community pieces
        #top is for opponent pieces
            #if number of players is greater than 2, top section is split into sections for number of opponents
            #opponent pieces are not visible to the player
        #bottom is for personal pieces
        #middle is for the game board
            #land pieces are brown
            #water pieces are blue
            #citadel pieces are grey
            #grid only shows land +3 tiles from land pieces, and adjusts size accordingly
#---------------------------------------------------------------End Game Phase------------------------------------------------
def end_game_phase():
    #display end_game_message
    #if yes selected, go back to configuration phase
    #if no, exit game

def end_game_phase_UI():
    #pop up over game_play_phase_UI with buttons for yes/no.

        
#---------------------------------------------------------------Game Loop------------------------------------------------
def game_loop():
    while True:
        configuration_phase()
        board_creation_phase()
        piece_selection_phase()
        game_play_phase()
        end_game_phase()