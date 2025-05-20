from __future__ import annotations
from typing import Callable, overload, TYPE_CHECKING, Literal, Self
from .util import BoolWithReason, Layer, Coordinate
from .entity import Entity
import os

if TYPE_CHECKING:
    from .board import Tile
    from .player import Player
    

class Action():
    '''An action that can be performed by a piece.

    Args:
        name: The name of the action.
        description: The description of the action.
    '''
    def __init__(self, name:str, description:str, action:Callable[[Tile, Player], None], can_use:Callable[[Tile, Player], BoolWithReason]):
        self.name = name
        self.description = description
        self.execute = action
        self.can_use = can_use


class ActionList(dict[str, Action]):
    '''A collection of actions that can be performed by a piece.
    '''
    def __init__(self, target:Tile, player:Player):
        '''Create a new action list.

        Args:
            target: The tile to perform the action on.
            player: The player using the piece.
        '''
        super().__init__()
        self.target = target
        self.player = player


    @overload
    def add(self, name:str, description:str, action:Callable[[Tile, Player], None], can_use:Callable[[Tile, Player], BoolWithReason]):
        '''Add an action to the list.
        
        Args:
            name: The name of the action.
            description: The description of the action.
            action: The action to add.
            can_use: A BoolWithReason indicating if the action can be used.
        '''
    @overload
    def add(self, action:Action):
        '''Add an action to the list.

        Args:
            action: The action to add.
        '''
    def add(self, name, description=None, action=None, can_use=None):
        if isinstance(name, Action):
            self[name.name] = name
        else:
            self[name] = Action(name, description, action, can_use)
    

    def __getitem__(self, key) -> Action:
        return super().__getitem__(key)
    

    def usable_actions(self) -> 'ActionList':
        '''Filter the actions to only those that can be used.
        '''
        usable = ActionList()
        for name, action in self.items():
            if action.can_use(self.target, self.player):
                usable[name] = action
        return usable


class Piece(Entity):
    '''The primary moveable entity in the game.
    '''


class Bird(Piece):
    abbreviation = "🐦"
    img = "bird.png"

    def actions(self, target:Tile, player:Player) -> ActionList:
        res = ActionList(target, player)
        res.add("move", "Move in a straight line", self.move, self.can_move)
        res.add("capture", "Capture a piece", self.capture, self.can_capture)
        res.add("place", "Place a Bird", self.place, self.can_place)
        return res
    

    def can_move(self, target:Tile, player:Player) -> BoolWithReason:
        # The Bird moves in a straight line, either horizontally or vertically, for as many tiles as you want.
        # It cannot move diagonally.
        if self.board != target.board:
            return BoolWithReason(f"{self} is not on the board with {target}")

        movement = self.get_vector_to(target)
        if not movement.is_straight():
            return BoolWithReason("Bird can only move in a straight line")

        return self.game.can_move(self, target, player)
    

    def can_capture(self, target:Tile, player:Player) -> BoolWithReason:
        # The Bird can capture any piece it lands on during its move.
        if self.board != target.board:
            return BoolWithReason(f"{self} is not on the board with {target}")

        movement = self.get_vector_to(target)
        if not movement.is_straight():
            return BoolWithReason("Bird can only capture in a straight line")
        
        return self.game.can_capture(self, target, player)
    

    def capture(self, target, player):
        # The Bird takes the place of the captured piece when it captures.
        super().capture(target, player)
        self.move(target, player)

        

class Knight(Piece):
    abbreviation = "♞"
    img = "shield.png"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        res = ActionList(target, player)
        res.add("move", "Move one square", self.move, self.can_move)
        res.add("capture", "Capture a piece", self.capture, self.can_capture)
        res.add("place", "Place a Knight", self.place, self.can_place)
        return res
    

    def can_move(self, target:Tile, player:Player) -> BoolWithReason:
        # The Knight moves one square at a time, either orthogonally (up, down, left, right) or diagonally.
        if self.board != target.board:
            return BoolWithReason(f"{self} is not on the board with {target}")
        if not target.coordinate in self.coordinate.get_adjacent_coordinates():
            return BoolWithReason(f"{self} can only move one square at a time")

        return self.game.can_move(self, target, player)


    def capture(self, target, player):
        # The Knight takes the place of the captured piece.
        super().capture(target, player)
        self.move(target, player)
    

    def can_capture(self, target:Tile, player:Player) -> BoolWithReason:
        # The Knight captures any piece it lands on during its move.
        if self.board != target.board:
            return BoolWithReason(f"{self} is not the board with {target}")
        
        if not target.coordinate in self.coordinate.get_adjacent_coordinates():
            return BoolWithReason(f"{self} cannot capture at {target}; it is more than one square away")

        return self.game.can_capture(self, target, player)
        


class Turtle(Piece):
    layer = Layer.TERRAIN
    abbreviation = "🐢"
    img = "turtle.png"

    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList(target, player)


class Rabbit(Piece):
    abbreviation = "🐇"
    img = "rabbit.png"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList(target, player)


class Builder(Piece):
    abbreviation = "🙎"
    img = "pickaxe.png"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList(target, player)


class Bomber(Piece):
    abbreviation = "💣"
    img = "bomb.png"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList(target, player)


class Necromancer(Piece):
    abbreviation = "🧙‍♂️"
    img = "skull.png"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList(target, player)


class Assassin(Piece):
    abbreviation = "🗡️"
    img = "crosshair.png"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList(target, player)


all_pieces = [
    Bird,
    Knight,
    Turtle,
    Rabbit,
    Builder,
    Bomber,
    Necromancer,
    Assassin
    ]



class Land(Entity):
    '''A land entity. Most pieces are placed on tiles with land.
    '''
    color = None
    layer = Layer.TERRAIN

    @property
    def img(self) -> str:
        from .board import Tile
        if isinstance(self.location, Tile):
            def get_fancy_img():
                elevations = []
                for dir in [Coordinate(-1, 0), Coordinate(0, -1), Coordinate(1, 0), Coordinate(0, 1)]:
                    elevation = self.get_edge_elevation(dir)
                    elevations.append(elevation)
                avg_elevation = sum(elevations) // len(elevations)
                elevations_str = ''.join(map(str, elevations))
                print(self.location.coordinate, elevations_str)
                if avg_elevation == 0:
                    return f"beach{elevations_str}.png"
                return "beach1111.png"
            fancy = get_fancy_img()
            if os.path.exists(f"img/{fancy}"):
                return fancy
        return "beach1111.png"
    

    def get_edge_elevation(self, direction:Coordinate) -> int:
        '''Get the type of edge in the given direction.
        
        Args:
            direction: The direction to check.
        
        Returns:
            The type of edge in the given direction.
        '''
        from .board import Tile
        if not isinstance(self.location, Tile):
            return 0
        tile:Tile = self.location.board[self.location.coordinate + direction]
        if not tile.has_type(Land):
            return 0
        adjacent = tile.get_adjacent_tiles()
        water = len([t for t in adjacent if t.is_water])
        if water == 0:
            return 2
        return 1


    def actions(self, target:Tile, player:Player) -> ActionList:
        res = ActionList(target, player)
        res.add("place", "Place a land tile", self.place, self.can_place)
        return res
    

    def can_place(self, target:Tile, player:Player) -> BoolWithReason:

        is_adjacent_to_land = any([tile.has_type(Land) for tile in target.get_adjacent_tiles()])
        board_has_no_land = len(self.game.board.where(Land)) == 0

        if not (is_adjacent_to_land or board_has_no_land):
            return BoolWithReason("Land tile must be placed adjacent to another land tile")

        return self.game.can_place(self, target, player)



class Citadel(Entity):
    '''A citadel. Citadels spawn pieces. Capturing a citadel is the primary goal of the game.
    '''
    abbreviation = "⛃"
    img = "building-2.png"

    def actions(self, target:Tile, player:Player) -> ActionList:
        res = ActionList(target, player)
        res.add("place", "Place a Citadel", self.place, self.can_place)

        return res


    def can_place(self, target:Tile, player:Player) -> BoolWithReason:
        # Citadels must be placed such that all citadels remain connected.
        
        new_game = self.simulate('place', target, player)

        if not new_game.board.citadels_are_connected:
            return BoolWithReason("Citadels must be connected.")
        
        return self.game.can_place(self, target, player)