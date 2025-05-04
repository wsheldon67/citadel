from __future__ import annotations
from typing import NamedTuple, Iterator, Generic, TypeVar, Literal, overload, Type, TypedDict
from typing import Callable
from abc import abstractmethod, ABC
from enum import Enum
import json


class BoolWithReason():
    '''A string that can be used as a boolean with a reason.
    '''
    def __init__(self, value:Literal[True]|str):
        '''Create a new BoolWithReason.

        Args:
            value: True, or a string that describes the reason for failure.
        '''
        if isinstance(value, str):
            self.reason = value
            self.value = False
        else:
            self.reason = None
            self.value = True
        
    def __bool__(self) -> bool:
        return self.value
    
    def __repr__(self) -> str:
        return f"BoolWithReason({self.value or self.reason})"


class Layer(Enum):
    '''The layer of an entity.'''
    TERRAIN = 0
    PIECE = 1


T = TypeVar('T', bound='Entity')


class ActionError(Exception):
    pass

class PlacementError(ActionError):
    pass


class GamePhase(Enum):
    '''The phase of the game.'''
    LAND_PLACEMENT = 0
    CITADEL_PLACEMENT = 1
    PIECE_SELECTION = 2
    BATTLE = 3
    END = 4


class Coordinate(NamedTuple):
    '''A coordinate on the board.'''
    x: int
    y: int


    def to_json(self) -> str:
        return f"{self.x},{self.y}"
    

    @classmethod
    def from_json(cls, json_data:str) -> 'Coordinate':
        x, y = json_data.split(',')
        return cls(int(x), int(y))
    

    def get_adjacent_coordinates(self, orthagonal:bool=True, diagonal:bool=True) -> list['Coordinate']:
        '''Get the coordinates adjacent to this coordinate.

        Args:
            orthagonal: If True, include orthagonal coordinates.
            diagonal: If True, include diagonal coordinates.
        '''
        if not orthagonal and not diagonal:
            raise ValueError("At least one of orthagonal or diagonal must be True.")
        coordinates = []
        if orthagonal:
            coordinates.append(Coordinate(self.x-1, self.y))
            coordinates.append(Coordinate(self.x+1, self.y))
            coordinates.append(Coordinate(self.x, self.y-1))
            coordinates.append(Coordinate(self.x, self.y+1))
        if diagonal:
            coordinates.append(Coordinate(self.x-1, self.y-1))
            coordinates.append(Coordinate(self.x-1, self.y+1))
            coordinates.append(Coordinate(self.x+1, self.y-1))
            coordinates.append(Coordinate(self.x+1, self.y+1))
        return coordinates
    
    def __sub__(self, other:'Coordinate') -> 'Coordinate':
        '''Subtract two coordinates.'''
        return Coordinate(self.x - other.x, self.y - other.y)
    
    def __add__(self, other:'Coordinate') -> 'Coordinate':
        '''Add two coordinates.'''
        return Coordinate(self.x + other.x, self.y + other.y)

    def __str__(self):
        return f"({self.x}, {self.y})"



class Rectangle(NamedTuple):
    '''A rectangle on the board.'''
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    @property
    def width(self) -> int:
        '''The width of the rectangle.'''
        return self.x_max - self.x_min + 1
    @property
    def height(self) -> int:
        '''The height of the rectangle.'''
        return self.y_max - self.y_min + 1
    
    def add_margin(self, margin:int) -> Rectangle:
        '''Add a margin to the rectangle, returning a larger rectangle.

        Args:
            margin: The amount of margin to add.
        '''
        return Rectangle(
            self.x_min - margin,
            self.x_max + margin,
            self.y_min - margin,
            self.y_max + margin
            )



class Game():
    '''The whole game.
    '''
    _player_rotations = [90, 270, 0, 180]
    def __init__(self, number_of_players:int=2, lands_per_player:int=5, personal_pieces_per_player:int=3, community_pieces_per_player:int=3):
        '''Create a new game.

        Args:
            number_of_players: The number of players in the game.
            lands_per_player: The number of lands per player.
            personal_pieces_per_player: The number of personal pieces each player starts with.
            community_pieces_per_player: The number of community pieces each player may choose.
        '''
        #: The number of lands each player places during the LAND_PLACEMENT phase.
        self.lands_per_player:int = lands_per_player
        #: The number of personal pieces each chooses during the PIECE_SELECTION phase.
        self.personal_pieces_per_player:int = personal_pieces_per_player
        #: The number of community pieces each chooses during the PIECE_SELECTION phase.
        self.community_pieces_per_player:int = community_pieces_per_player
        #: The number of citadels each player places during the CITADEL_PLACEMENT phase.
        self.citadels_per_player:int = 1
        #: The players in the game.
        self.players:list[Player] = []
        #: The main game board.
        self.board = Board(self)
        #: The current turn. This number should continuously increase; it does not reset between rounds.
        self.turn:int = 0
        #: The pieces that are available to any player to place onto a board.
        self.community_pool:EntityList[Piece] = EntityList(self, name='Community Pool')
        #: The pieces that have been captured.
        self.graveyard:EntityList[Piece] = EntityList(self, name='Graveyard')
        

        for i in range(number_of_players):
            new_player = Player(f"Player {i}", self)
            new_player.rotation = self._player_rotations[i]
            self.players.append(new_player)

        for i in range(self.lands_per_player):
            for player in self.players:
                land = Land(player.personal_stash, player)
                player.personal_stash.append(land)
        for i in range(self.citadels_per_player):
            for player in self.players:
                citadel = Citadel(player.personal_stash, player, player)
                player.personal_stash.append(citadel)

    
    class GameJson(TypedDict):
        lands_per_player: int
        personal_pieces_per_player: int
        community_pieces_per_player: int
        citadels_per_player: int
        players: list[Player.PlayerJson]
        board: Board.BoardJson
        turn: int
        community_pool: EntityList.EntityListJson
        graveyard: EntityList.EntityListJson

    
    def to_json(self) -> GameJson:
        '''Convert the game to JSON.
        '''
        return {
            'lands_per_player': self.lands_per_player,
            'personal_pieces_per_player': self.personal_pieces_per_player,
            'community_pieces_per_player': self.community_pieces_per_player,
            'citadels_per_player': self.citadels_per_player,
            'players': [player.to_json() for player in self.players],
            'board': self.board.to_json(),
            'turn': self.turn,
            'community_pool': self.community_pool.to_json(),
            'graveyard': self.graveyard.to_json(),
            }
    

    @classmethod
    def from_json(cls, json_data:GameJson):
        '''Load the game from JSON.

        Args:
            json_data: The JSON data to load.
        '''
        game = cls(
            len(json_data['players']),
            json_data['lands_per_player'],
            json_data['personal_pieces_per_player'],
            json_data['community_pieces_per_player'],
            )
        game.citadels_per_player = json_data['citadels_per_player']
        game.players = [Player.from_json(player_data, game) for player_data in json_data['players']]
        game.board = Board.from_json(json_data['board'], game)
        game.turn = json_data['turn']
        game.community_pool = EntityList.from_json(json_data['community_pool'], game)
        game.graveyard = EntityList.from_json(json_data['graveyard'], game)
        return game


    @property
    def current_player(self) -> 'Player':
        '''The player whose turn it is.
        '''
        return self.players[self.turn % len(self.players)]
    

    def end_turn(self):
        '''End the current player's turn.
        '''
        self.turn += 1
    

    @property
    def phase(self) -> GamePhase:
        '''The current phase of the game.
        '''
        if not all([player.is_done_placing_lands for player in self.players]):
            return GamePhase.LAND_PLACEMENT
        if not all([player.is_done_placing_citadels for player in self.players]):
            return GamePhase.CITADEL_PLACEMENT
        if not all([player.is_done_choosing_pieces for player in self.players]):
            return GamePhase.PIECE_SELECTION
        if not self.winner:
            return GamePhase.BATTLE
        return GamePhase.END
    

    @property
    def winner(self) -> Player|None:
        '''The winner of the game, if any.
        '''
        has_citadels = [len(player.citadels) > 0 for player in self.players]
        if sum(has_citadels) == 1:
            return self.players[has_citadels.index(True)]
        return None
    

    def _repr_html_(self) -> str:
        return f"""<div>
        {self.community_pool._repr_html_()}
        <div style='display: flex; flex-direction: row;'>
            {self.players[0]._repr_html_()}
            {self.board._repr_html_()}
            {self.players[1]._repr_html_()}
        </div>
        {self.graveyard._repr_html_()}
        <p>Current Player: {self.current_player.name}</p>
        <p>Phase: {self.phase.name}</p>
        </div>"""
    

    def can_move(self, piece:'Piece', target:'Tile', player:'Player') -> BoolWithReason:
        '''Check if a piece can be moved to the given tile.

        Args:
            piece: The piece to move.
            target: The tile to move the piece to.
        '''
        can_add_to_tile = self.board[target.coordinate].can_add(piece)
        if not can_add_to_tile:
            return BoolWithReason(f"cannot add {piece} to {target}: {can_add_to_tile.reason}")
    
        if piece.owner != player:
            return BoolWithReason(f"Cannot move {piece}: not owned by player '{player.name}'.")

        new_board = self.board.copy()
        new_board.place(piece, target.coordinate, to_test=True)
        
        if not new_board.citadels_are_connected:
            return BoolWithReason("move would disconnect citadels")

        return BoolWithReason(True)


    def move(self, piece:'Piece', target:'Tile', player:'Player'):
        '''Move a piece to the given tile.

        Args:
            piece: The piece to move.
            target: The tile to move the piece to.
            player: The player moving the piece.
        '''
        can_move = self.can_move(piece, target, player)
        if not can_move:
            raise PlacementError(f"Cannot move {piece} to {target}: {can_move.reason}")
        piece.location.remove(piece)
        target.append(piece)
    

    def can_place(self, entity:'Entity', target:'Tile', player:'Player') -> BoolWithReason:
        '''Check if an entity can be placed on the given tile.

        Args:
            entity: The entity to place.
            target: The tile to place the entity on.
        '''
        can_add_to_tile = self.board[target.coordinate].can_add(entity)
        if not can_add_to_tile:
            return BoolWithReason(f"cannot add {entity} to {target}: {can_add_to_tile.reason}")
    
        if not entity in player.placeable_entities:
            return BoolWithReason(f"Player '{self}' does not have access to place {entity}.")
    
        if isinstance(entity, Piece) and not player.is_adjacent_to_citadel(target):
            return BoolWithReason(f"Cannot place {entity} at {target}: not adjacent to any of player's citadels.")

        return BoolWithReason(True)


    def place(self, entity:'Entity', target:'Tile', player:'Player'):
        '''Place an entity on the given tile.

        Args:
            entity: The entity to place.
            target: The tile to place the entity on.
        '''
        if not isinstance(entity, Entity):
            raise TypeError(f"Can only place an Entity, not {type(entity)}.")
        can_place = self.can_place(entity, target, player)
        if not can_place:
            raise PlacementError(f"Cannot place {entity} on {target}: {can_place.reason}")
        entity.owner = player
        entity.location.remove(entity)
        target.append(entity)


    def can_capture(self, entity:'Entity', target:'Tile', player:'Player') -> BoolWithReason:
        '''Check if an entity can capture another entity.

        Args:
            entity: The entity to capture with.
            target: The tile to attempt capture on.
            player: The player attempting the capture.
        '''
        if not target.where(Piece):
            return BoolWithReason(f"Cannot capture at {target}: no pieces to capture.")

        return BoolWithReason(True)
    

    def capture(self, entity:'Entity', target:'Tile', player:'Player'):
        '''Capture an entity, sending it to the graveyard.'''
        can_capture = self.can_capture(entity, target, player)
        if not can_capture:
            raise PlacementError(f"Cannot capture {target} with {entity}: {can_capture.reason}")
        entity = target.where(Piece)[0]
        self.graveyard.append(entity)
        self.board.remove(entity)



class Player():
    '''A player in the game.
    '''
    def __init__(self, name:str, game:Game):
        '''
        Args:
            game: The game this player is in.
        '''
        self.name:str = name
        self.personal_stash:EntityList['Piece'] = EntityList(game, name=f"{name}'s Personal Stash")
        self.game:Game = game
        self.rotation:int = 0
    

    class PlayerJson(TypedDict):
        name: str
        personal_stash: EntityList.EntityListJson
        rotation: int
    

    def to_json(self) -> dict:
        '''Convert the player to JSON.
        '''
        return {
            'name': self.name,
            'personal_stash': self.personal_stash.to_json(),
            'rotation': self.rotation,
            }
    

    @classmethod
    def from_json(cls, json_data:dict, game:Game) -> 'Player':
        '''Load the player from JSON.

        Args:
            json_data: The JSON data to load.
            game: The game this player is in.
        '''
        player = cls(json_data['name'], game)
        player.personal_stash = EntityList.from_json(json_data['personal_stash'], game)
        player.rotation = json_data['rotation']
        return player

    
    @property
    def placeable_entities(self) -> EntityList['Entity']:
        '''The entity lists this player can place from.
        '''
        return self.personal_stash + self.game.community_pool
    

    @property
    def community_entities(self) -> 'EntityList[Piece]':
        '''The pieces in the community pool that this player created.
        '''
        return self.game.community_pool.where(Piece, self)


    @property
    def is_done_choosing_personal_pieces(self) -> bool:
        '''True if the player has chosen all of their personal pieces.
        '''
        personal_pieces = self.personal_stash.where(Piece)
        return len(personal_pieces) >= self.game.personal_pieces_per_player


    @property
    def is_done_choosing_community_pieces(self) -> bool:
        '''True if the player has chosen all of their community pieces.
        '''
        community_pieces = self.community_entities.where(Piece)
        return len(community_pieces) >= self.game.community_pieces_per_player


    @property
    def is_done_choosing_pieces(self) -> bool:
        '''True if the player has chosen all of their pieces.
        '''
        return self.is_done_choosing_personal_pieces and self.is_done_choosing_community_pieces


    def choose_community_piece(self, piece:'Piece'|Type['Piece']):
        '''Choose a piece for the community pool.
        '''
        if self.is_done_choosing_community_pieces:
            raise ValueError(f"Players are not allowed to choose more than {self.game.community_pieces_per_player} pieces for the community pool. '{self.name}' has already chosen {len(self.community_entities)} community pieces.")
        
        if isinstance(piece, type):
            piece = piece(self.game.community_pool, self)
        
        piece.created_by = self
        self.game.community_pool.append(piece)

    
    def choose_personal_piece(self, piece:'Piece'|Type['Piece']):
        '''Choose a piece for the personal stash.
        '''
        if self.is_done_choosing_personal_pieces:
            raise ValueError(f"Players are not allowed to choose more than {self.game.personal_pieces_per_player} pieces for their personal stash. '{self.name}' has already chosen {len(self.personal_stash.where(Piece))} personal pieces.")
        
        if isinstance(piece, type):
            piece = piece(self.personal_stash, self, self)
        
        piece.created_by = self
        piece.owner = self
        self.personal_stash.append(piece)


    @property
    def land_tiles(self) -> 'EntityList[Land]':
        '''The land tiles this player has placed.
        '''
        player_lands = EntityList(self.game)
        for tile in self.game.board.values():
            if tile.land and tile.land.created_by == self:
                player_lands.append(tile.land)
        return player_lands
    

    @property
    def is_done_placing_lands(self) -> bool:
        '''True if the player has placed all of their lands.
        '''
        return len(self.land_tiles) >= self.game.lands_per_player
    

    @property
    def citadels(self) -> 'EntityList[Citadel]':
        '''The citadels this player has placed.
        '''
        return self.game.board.where(Citadel, owner=self)

    
    @property
    def is_done_placing_citadels(self) -> bool:
        '''True if the player has placed all of their citadels.
        '''
        return len(self.citadels) >= self.game.citadels_per_player

    
    def is_adjacent_to_citadel(self, to_test:Coordinate|Tile|Entity) -> bool:
        '''Check if the given object is adjacent to a citadel belonging to this player.

        Args:
            to_test: The Coordinate, Tile, or Entity to check.
        '''
        if isinstance(to_test, Coordinate):
            coordinate = to_test
        elif isinstance(to_test, Tile):
            coordinate = to_test.coordinate
        elif isinstance(to_test, Entity):
            coordinate = self.game.board.get_coordinate_of_entity(to_test)
        for citadel in self.citadels:
            citadel_coordinate = self.game.board.get_coordinate_of_entity(citadel)
            if coordinate in citadel_coordinate.get_adjacent_coordinates():
                return True
        return False
    
        
    def _repr_html_(self) -> str:
        return f"""<div style='display: flex; flex-direction: column;'>{self.name}{self.personal_stash._repr_html_()}</div>"""


    def __str__(self) -> str:
        return f"Player({self.name})"
    
    def __repr__(self) -> str:
        return f"Player({self.name})"


    def _to_tile(self, obj:Coordinate|Tile|Entity) -> Tile:
        '''Infer a Coordinate, Tile, or Entity to a Tile.

        Args:
            obj: The object to convert.
        '''
        if isinstance(obj, Coordinate):
            return self.game.board[obj]
        if isinstance(obj, Tile):
            return obj
        if isinstance(obj, Entity):
            return obj.location
        raise TypeError(f"Object must be a Coordinate, Tile, or Entity, not {type(obj)}.")
    

    def _to_entity(self, obj:Coordinate|Tile|Entity|Type['Entity']) -> 'Entity':
        '''Infer a Coordinate, Tile, or Entity to an Entity.
        
        Returns a board piece unless the object is a type, in which case it returns the first entity of that type in the player's personal stash.
        '''
        if isinstance(obj, Coordinate) or isinstance(obj, Tile):
            if isinstance(obj, Coordinate):
                obj = self.game.board[obj]
            entities = obj.where(owner=self)
            if len(entities) > 1:
                entities = entities.where(Piece)
            if not entities:
                raise ActionError(f"No entities found at {obj}.")
            return entities[0]
        if isinstance(obj, Entity):
            return obj
        if isinstance(obj, type):
            entities = self.personal_stash.where(obj)
            if not entities:
                raise ActionError(f"Entity '{obj}' not found in personal stash.")
            return entities[0]


    def can_perform_action(self, entity:'Entity'|Type['Entity'], action_name:str, target:Coordinate|Tile|Entity) -> BoolWithReason:
        '''Check if an entity can perform an action.

        Args:
            entity: The entity to perform the action on.
            action_name: The name of the action to perform.
            target: The target of the action. This can be a coordinate, tile, or entity.
        '''
        target = self._to_tile(target)
        entity = self._to_entity(entity)
        
        actions = entity.actions(target, self)
        if action_name not in actions:
            return BoolWithReason(f"Action '{action_name}' not found on {entity}.")
        
        return actions[action_name].can_use
    

    def perform_action(self, entity:'Entity'|Type['Entity']|Coordinate|Tile, action_name:str, target:Coordinate|Tile|Entity):
        '''Perform an action on an entity.

        Args:
            entity: The entity to perform the action on.
            action_name: The name of the action to perform.
            target: The target of the action. This can be a coordinate, tile, or entity.
        '''
        target = self._to_tile(target)
        entity = self._to_entity(entity)
        
        can_perform = self.can_perform_action(entity, action_name, target)
        if not can_perform:
            raise ActionError(can_perform.reason)
        action = entity.actions(target, self)[action_name]
        action.execute(target, self)
        entity.game.end_turn()
    

    def place(self, entity:'Entity'|Type['Entity'], target:Coordinate|Tile|Entity):
        self.perform_action(entity, 'place', target)
    
    def move(self, entity:'Entity'|Type['Entity']|Coordinate|Tile, target:Coordinate|Tile|Entity):
        self.perform_action(entity, 'move', target)
    
    def capture(self, entity:'Entity'|Type['Entity']|Coordinate|Tile, target:Coordinate|Tile|Entity):
        self.perform_action(entity, 'capture', target)


class Board(dict[Coordinate, 'Tile']):
    '''A collection of tiles.
    '''

    def __init__(self, game:Game, name:str='main'):
        '''Create a new board.

        Args:
            game: The game this board is in.
            name: A unique name for this board.
        '''
        super().__init__()
        self.name = name
        self.game:Game = game
        self.default_tile_color = "#87CEEB"
    

    class BoardJson(TypedDict):
        name: str
        tiles: dict[tuple[int, int], Tile.EntityListJson]
    

    def to_json(self) -> dict:
        '''Convert the board to JSON.
        '''
        return {
            'name': self.name,
            'tiles': {coordinate.to_json(): tile.to_json() for coordinate, tile in self.items()},
            }


    @classmethod
    def from_json(cls, json_data:dict, game:Game) -> 'Board':
        '''Load the board from JSON.

        Args:
            json_data: The JSON data to load.
            game: The game this board is in.
        '''
        board = cls(game, json_data['name'])
        for coordinate, tile_data in json_data['tiles'].items():
            coordinate = Coordinate.from_json(coordinate)
            tile:Tile = Tile.from_json(tile_data, board)
            tile.coordinate = coordinate
            board[coordinate] = tile
        return board


    def __hash__(self) -> int:
        return hash(self.name)
    

    def __eq__(self, other:object) -> bool:
        if not isinstance(other, Board):
            return False
        return self.name == other.name

    @overload
    def __getitem__(self, coordinate:Coordinate) -> 'Tile':
        '''Get the tile at the given coordinate.

        Args:
            coordinate: The coordinate to get the tile at.
        '''
    @overload
    def __getitem__(self, coordinates:list[Coordinate]) -> list['Tile']:
        '''Get the tiles at the given coordinates.

        Args:
            coordinates: The coordinates to get the tiles at.
        '''
    def __getitem__(self, coordinate:list[Coordinate|tuple[int, int]]|Coordinate|tuple[int, int]):
        if isinstance(coordinate, list):
            res = []
            for coord in coordinate:
                if not isinstance(coord, Coordinate):
                    coord = Coordinate(*coord)
                res.append(self.get(coord, Tile(self, coord)))
            return res
        elif isinstance(coordinate, Coordinate):
            return super().get(coordinate, Tile(self, coordinate))
        elif isinstance(coordinate, tuple):
            coord = Coordinate(*coordinate)
            return super().get(coord, Tile(self, coord))
        else:
            raise TypeError(f"Coordinate must be a Coordinate or list of Coordinates, not {type(coordinate)}.")
        
    
    def __contains__(self, key):
        if isinstance(key, Coordinate):
            return super().__contains__(key)
        elif isinstance(key, Tile):
            return super().__contains__(key.coordinate)
        elif isinstance(key, Entity):
            return self.get_coordinate_of_entity(key) is not None
        else:
            raise TypeError(f"Key must be a Coordinate, Tile, or Entity, not {type(key)}.")
        
    
    def copy(self) -> 'Board':
        '''Create a copy of the board.

        Returns:
            A copy of the board.
        '''
        new_board = Board(self.game)
        for coordinate, tile in self.items():
            new_tile = Tile(new_board, coordinate)
            new_tile.extend(tile)
            new_board[coordinate] = new_tile
        return new_board
    

    def place(self, entity:'Entity', coordinate:Coordinate, to_test:bool=False):
        '''Place an entity on the board.

        Args:
            entity: The entity to place.
            coordinate: The coordinate to place the entity at.
            to_test: If True, force the placement and do not change the entity.
        '''
        if coordinate not in self:
            self[coordinate] = Tile(self, coordinate)
        if not to_test:
            entity.location = self[coordinate]
        self[coordinate].append(entity, not to_test)
    

    def get_coordinate_of_entity(self, entity:'Entity') -> Coordinate|None:
        '''Get the coordinate of an entity.

        Args:
            entity: The entity to get the coordinate of.
        '''
        for coordinate, tile in self.items():
            if entity in tile:
                return coordinate
        return None
    

    def remove(self, entity:'Entity') -> 'Entity':
        '''Remove an entity from the board.

        Args:
            entity: The entity to remove.
        '''
        coordinate = self.get_coordinate_of_entity(entity)
        if coordinate is None:
            raise ValueError(f"Entity '{entity}' not found on board.")
        self[coordinate].remove(entity)
        if not self[coordinate]:
            del self[coordinate]
    

    def where(self,
        entity_type:Type[T]=Type['Entity'],
        created_by:Player|None=None,
        owner:Player|None=None,
        layer:Layer|None=None) -> 'EntityList[T]':
        '''Search for entities on the board.

        If any arguments are not provided, all entities for that parameter are returned.
        
        Args:
            entity_type: The type of entity to find.
            created_by: The player who created the entity.
            owner: The player who owns the entity.
            layer: The layer of the entity.
        '''
        entities = EntityList(self.game)
        for tile in self.values():
            entities.extend(tile.where(entity_type, created_by, owner, layer))
        return entities


    def find_tiles(self,
        entity_type:Type['Entity']=Type['Entity'],
        created_by:Player|None=None,
        layer:Layer|None=None) -> list['Tile']:
        '''Search for tiles on the board.

        If any arguments are not provided, all entities for that parameter are returned.
        
        Args:
            entity_type: The type of entity to find.
            created_by: The player who created the entity.
            layer: The layer of the entity.
        '''
        tiles = []
        for tile in self.values():
            for entity in tile:
                if not isinstance(entity, entity_type):
                    continue
                if created_by and entity.created_by != created_by:
                    continue
                if layer and entity.layer != layer:
                    continue
                tiles.append(tile)
        return tiles
    

    @property
    def citadels(self) -> 'EntityList[Citadel]':
        '''The citadels on the board.
        '''
        return self.where(Citadel)


    @property
    def citadels_are_connected(self) -> bool:
        '''True if all citadels are connected to each other by a series of land tiles.
        
        Diagonals do no count, but Turtles do. This value is also True if there are not at least 2 citadels on the board.
        '''
        if len(self.citadels) <= 1:
            return True
        starting_citadel = self.find_tiles(Citadel)[0]
        connected_citadels = set()
        checked_tiles = set()
        def walk(tile:Tile):
            if tile in checked_tiles:
                return
            checked_tiles.add(tile)
            if tile.has_type(Citadel):
                connected_citadels.add(tile.citadel)
            if len(connected_citadels) == len(self.citadels):
                return
            if tile.get_by_layer(Layer.TERRAIN):
                for adjacent_tile in tile.get_adjacent_tiles(diagonal=False):
                    walk(adjacent_tile)
        walk(starting_citadel)
        return len(connected_citadels) == len(self.citadels)


    @property
    def extents(self) -> Rectangle:
        '''The extents of the board. The extents are the minimum and maximum x and y coordinates of the tiles on the board.
        '''
        min_x = min_y = None
        max_x = max_y = None
        for coordinate in self.keys():
            if min_x is None or coordinate.x < min_x:
                min_x = coordinate.x
            if max_x is None or coordinate.x > max_x:
                max_x = coordinate.x
            if min_y is None or coordinate.y < min_y:
                min_y = coordinate.y
            if max_y is None or coordinate.y > max_y:
                max_y = coordinate.y
        return Rectangle(min_x, max_x, min_y, max_y)
    

    def _repr_html_(self) -> str:
        '''Get a string representation of the board for debugging.
        '''
        if self.extents.x_min is None:
            return "<p>Board is empty</p>"
        rows = []
        if self.extents.x_min < -100 or self.extents.x_max > 100:
            raise ValueError(f"Board is too large to display in HTML (x: {self.extents.x_min} - {self.extents.x_max}). Use a smaller board.")
        if self.extents.y_min < -100 or self.extents.y_max > 100:
            raise ValueError(f"Board is too large to display in HTML (y: {self.extents.y_min} - {self.extents.y_max}). Use a smaller board.")
        
        first_row = []
        for y in range(int(self.extents.y_min), int(self.extents.y_max) + 1):
            first_row.append(f"<th>y{y}</th>")
        rows.append(f"<tr style='height: 36px;'><th></th>{''.join(first_row)}</tr>")
        
        for x in range(int(self.extents.x_min), int(self.extents.x_max) + 1):
            cells = []
            for y in range(int(self.extents.y_min), int(self.extents.y_max) + 1):
                coordinate = Coordinate(x, y)
                color, abbreviation, rotation = self[coordinate].short_html
                cells.append(f"<td style='background-color: {color}; transform: rotate({rotation}deg); width: 58px; height 58px; border: 1px solid white; color: black; text-align: center; font-size: 1.5rem; padding: 0; margin: 0;'>{abbreviation}</td>")
            rows.append(f"<tr style='height: 60px;'><th>x{x}</th>{''.join(cells)}</tr>")
        return f"<table style='table-layout: fixed;'>{''.join(rows)}</table>"
    

    def get_vector(self, start:Coordinate, end:Coordinate) -> Vector:
        '''Get a vector from the start to the end coordinate.

        Args:
            start: The starting coordinate of the vector.
            end: The ending coordinate of the vector.
        '''
        return Vector(self, start, end)
    

    def get_equivalent_entity(self, entity:Entity) -> Entity|None:
        '''Get the equivalent entity on the board.

        The equivalent entity is an entity of the same type, coordinate, and owner.

        Args:
            entity: The entity to get the equivalent of.
        '''

        for tile in self.values():
            for e in tile:
                if isinstance(e, type(entity)) and e.coordinate == entity.coordinate and e.owner == entity.owner:
                    return e
        return None


class Vector():
    '''An object that represents two coordinates on the board, where one of them is the starting coordinate.'''
    def __init__(self, board:Board, start:Coordinate, end:Coordinate):
        '''Create a new vector.

        Args:
            board: The board this vector is on.
            start: The starting coordinate of the vector.
            end: The ending coordinate of the vector.
        '''
        self.board = board
        self.start = start
        self.end = end
    

    def is_straight(self) -> bool:
        '''Check if the vector is a straight line.'''
        return self.start.x == self.end.x or self.start.y == self.end.y
    

    def is_diagonal(self) -> bool:
        '''Check if the vector is a diagonal line.'''
        return abs(self.start.x - self.end.x) == abs(self.start.y - self.end.y)


U = TypeVar('U', bound='Entity')


class EntityList(list, Generic[T]):
    '''A collection of entities.
    '''

    def __init__(self, game:Game, entities:list[T]=[], name:str|None=None):
        '''Create a new entity list.

        Args:
            game: The game this entity list is in.
            entities: The entities to add to the list.
            name: A unique name for this entity list.
        '''
        super().__init__(entities)
        self.name = name
        self.game = game

    
    class EntityListJson(TypedDict):
        name: str
        entities: list[Entity.EntityJson]


    def to_json(self) -> EntityListJson:
        '''Convert the entity list to JSON.
        '''
        return {
            'name': self.name,
            'entities': [entity.to_json() for entity in self]
            }
    

    @classmethod
    def from_json(cls, json_data:EntityListJson, game:Game) -> 'EntityList':
        '''Load the entity list from JSON.

        Args:
            json_data: The JSON data to load.
            game: The game this entity list is in.
        '''
        self = cls(game)
        self.name = json_data['name']
        entities = []
        for entity_data in json_data['entities']:
            entity_type = entity_data['type']
            created_by = next((player for player in game.players if player.name == entity_data['created_by']), None)
            owner = next((player for player in game.players if player.name == entity_data['owner']), None)
            entity = globals()[entity_type](self, created_by, owner)
            entities.append(entity)
        self.extend(entities)
        return self


    def __iter__(self) -> Iterator[T]:
        '''Iterate over the entities in the collection.
        '''
        return super().__iter__()
    
    
    def has_type(self, entity_type: Type['Entity']) -> bool:
        '''Check if the collection has an entity of the given type.

        Use like `if entities.has_type(Turtle):`

        Args:
            entity_type: The type of entity to check for.
        '''
        return any(isinstance(entity, entity_type) for entity in self)
    

    def where(self,
        entity_type: Type[U]=None,
        created_by: Player|None=None,
        owner: Player|None=None,
        layer: Layer|None=None) -> 'EntityList[U]':
        '''Search for entities in the collection.
        
        If any arguments are not provided, all entities for that parameter are returned.
        
        Args:
            entity_type: The type of entity to find.
            created_by: The player who created the entity.
            owner: The player who owns the entity.
            layer: The layer of the entity.
        '''
        entities = EntityList(self.game)
        for entity in self:
            if entity_type and not isinstance(entity, entity_type):
                continue
            if created_by and entity.created_by != created_by:
                continue
            if layer and entity.layer != layer:
                continue
            if owner and entity.owner != owner:
                continue
            entities.append(entity, reset_location=False)
        return entities
    

    def where_not(self,
        entity_type:Type['Entity']|None=None,
        created_by:Player|None=None,
        owner:Player|None=None,
        layer:Layer|None=None) -> 'EntityList':
        '''Get the entities in this list that do not match the given criteria.

        If any arguments are not provided, all entities for that parameter are returned.

        Args:
            entity_type: The type of entity to exclude.
            created_by: The player who created the entity to exclude.
            owner: The player who owns the entity to exclude.
            layer: The layer of the entity to exclude.
        '''
        entities = EntityList(self.game)
        for entity in self:
            if entity_type and isinstance(entity, entity_type):
                continue
            if created_by and entity.created_by == created_by:
                continue
            if layer and entity.layer == layer:
                continue
            if owner and entity.owner == owner:
                continue
            entities.append(entity)
        return entities
    

    def _repr_html_(self) -> str:
        res = []
        for entity in self:
            res.append(f"<div style='background-color: {entity.color}; font-size: 1.5rem;'>{entity.abbreviation}</div>")
        return f"<div style='display: flex; flex-wrap: wrap; width: 100px;'>{''.join(res)}</div>"


    def __getitem__(self, index:int) -> T:
        '''Get an entity by index.'''
        return super().__getitem__(index)
    

    def __str__(self) -> str:
        '''Get a string representation of the entity list.
        '''
        res = []
        for entity in self:
            res.append(str(entity))
        return f"EntityList:{self.name}({', '.join(res)})"
    
    def __repr__(self) -> str:
        return self.__str__()
    

    def append(self, object:'Entity', reset_location:bool=True):
        if reset_location:
            object.location = self
        return super().append(object)



class Tile(EntityList):
    '''A single tile (location) on the board.
    '''
    def __init__(self, board:Board, coordinate:Coordinate):
        '''Create a new tile.

        Args:
            board: The board this tile is on.
            coordinate: The coordinate of this tile.
        '''
        super().__init__(board.game, name=f"{board.name}{coordinate}")
        self.board = board
        self.coordinate = coordinate
    

    class TileJson(TypedDict):
        name: str
        coordinate: str
        entities: list[Entity.EntityJson]
    

    def to_json(self) -> TileJson:
        '''Convert the tile to JSON.
        '''
        return {
            'name': self.name,
            'coordinate': self.coordinate.to_json(),
            'entities': [entity.to_json() for entity in self],
            }
    

    @classmethod
    def from_json(cls, json_data:TileJson, board:Board) -> 'EntityList':
        '''Load the entity list from JSON.

        Args:
            json_data: The JSON data to load.
            game: The game this entity list is in.
        '''
        self = cls(board, Coordinate.from_json(json_data['coordinate']))
        self.name = json_data['name']
        entities = []
        for entity_data in json_data['entities']:
            entity_type = entity_data['type']
            created_by = next((player for player in self.game.players if player.name == entity_data['created_by']), None)
            owner = next((player for player in self.game.players if player.name == entity_data['owner']), None)
            entity = globals()[entity_type](self, created_by, owner)
            entities.append(entity)
        self.extend(entities)
        return self
    

    def __hash__(self) -> int:
        return hash((self.coordinate, self.board))


    def __eq__(self, other:object) -> bool:
        if not isinstance(other, Tile):
            return False
        return self.coordinate == other.coordinate and self.board == other.board
    

    def append(self, entity:Entity, reset_location:bool=True):
        can_add = self.can_add(entity)
        if can_add:
            super().append(entity, reset_location)
            self.board[self.coordinate] = self
        else:
            raise ValueError(f"Cannot add {entity.__class__.__name__} to tile at {self.coordinate}: {can_add}")
    

    def can_add(self, entity:Entity) -> BoolWithReason:
        '''Check if an entity can be added to this tile.

        This only checks tile-level constraints. Board.can_place_entity() and Board.can_move_piece()
        include board-level constraints, and Player.can_place_piece() and Player.can_move_piece() include player-level constraints.

        Args:
            entity: The entity to add.
        '''
        if self.get_by_layer(entity.layer):
            return BoolWithReason(f"layer {entity.layer.name} already occupied")
        
        if entity.layer.value > 0:
            layer_below = Layer(entity.layer.value - 1)
            if not self.get_by_layer(layer_below):
                return BoolWithReason(f"{entity.layer.name}-layer entities must be placed on top of a {layer_below.name}-layer entity")
    
        return BoolWithReason(True)
    

    def get_by_layer(self, layer:Layer) -> 'Entity'|None:
        '''Get the first entity of the given layer.

        Args:
            layer: The layer to get.
        '''
        for entity in self:
            if entity.layer == layer:
                return entity
        return None

    

    @property
    def land(self) -> 'Land'|None:
        '''The land tile on this tile, if any.
        '''
        for entity in self:
            if isinstance(entity, Land):
                return entity
        return None
    

    @property
    def piece(self) -> 'Piece'|None:
        '''The first piece on this tile, if any.
        '''
        for entity in self:
            if isinstance(entity, Piece):
                return entity
        return None
    

    @property
    def citadel(self) -> 'Citadel'|None:
        '''The citadel on this tile, if any.
        '''
        for entity in self:
            if isinstance(entity, Citadel):
                return entity
        return None


    @property
    def is_water(self) -> bool:
        '''True if the tile is water.'''
        return not self.has_type(Land)
    

    @property
    def has_entities(self) -> bool:
        '''True if the tile has any entities.'''
        return len(self) > 0
    

    def get_adjacent_tiles(self, orthagonal:bool=True, diagonal:bool=True) -> list['Tile']:
        '''Get the tiles adjacent to this tile.

        Args:
            orthagonal: If True, include orthagonal tiles.
            diagonal: If True, include diagonal tiles.
        '''
        coordinates = self.coordinate.get_adjacent_coordinates(orthagonal, diagonal)
        return self.board[coordinates]
    
    
    @property
    def short_html(self) -> tuple[str, str, str]:
        '''Return a css color representing the terrain layer, and single character representing the piece layer.
        '''
        terrain_layer = self.get_by_layer(Layer.TERRAIN)
        if terrain_layer:
            color = terrain_layer.color
        else:
            color = self.board.default_tile_color
        
        piece_layer = self.get_by_layer(Layer.PIECE)
        if piece_layer:
            abbreviation = piece_layer.abbreviation
            if piece_layer.owner:
                rotation = piece_layer.owner.rotation
            else:
                rotation = 0
        else:
            abbreviation = " "
            rotation = 0
        return color, abbreviation, str(rotation)
    

    @property
    def color(self) -> str:
        '''The color of the tile.
        '''
        return self.short_html[0]



class Entity(ABC):
    '''An game object that can be placed on a tile.

    Args:
        created_by: The player who created this entity.
        owner: The player who owns this entity.
        location: The EntityList this entity is in.
    '''
    layer:Layer = Layer.PIECE
    color:str = "#000000"
    abbreviation:str = " "

    def __init__(self, location:EntityList, created_by:Player|None=None, owner:Player|None=None):
        self.created_by:Player|None = created_by
        self.owner:Player|None = owner
        self.location:EntityList = location
        self.game:Game = location.game
    

    class EntityJson(TypedDict):
        type: str
        created_by: str|None
        owner: str|None


    def to_json(self) -> EntityJson:
        '''Convert the entity to JSON.
        '''
        return {
            'type': self.__class__.__name__,
            'created_by': self.created_by.name if self.created_by else None,
            'owner': self.owner.name if self.owner else None,
            }
    

    def __str__(self) -> str:
        res = self.__class__.__name__
        if self.location:
            if self.location.name:
                res += f"({self.location.name})"
        if self.owner:
            res += f"({self.owner.name})"
        return res
    

    def __repr__(self) -> str:
        return self.__str__()
    

    def copy(self) -> 'Entity':
        '''Create a copy of this entity.

        Returns:
            A copy of this entity.
        '''
        return self.__class__(self.created_by, self.owner, self.location)


    @property
    def board(self) -> Board|None:
        '''The board this entity is on.
        '''
        if not self.location:
            return None
        if isinstance(self.location, Tile):
            return self.location.board
    

    @property
    def coordinate(self) -> Coordinate|None:
        '''The coordinate of this piece on the board.
        '''
        if not self.location:
            return None
        if not isinstance(self.location, Tile):
            return None
        return self.location.coordinate
    

    def get_vector_to(self, target:'Tile') -> Vector:
        '''Get a vector from this entity to the target coordinate.

        Args:
            target: The target coordinate.
        '''
        if self.board != target.board:
            raise ValueError(f"Cannot get vector from {self} to {target}: not on the same board.")
        return self.board.get_vector(self.coordinate, target.coordinate)
    
    @abstractmethod
    def actions(self, target:Tile, player:Player) -> ActionList:
        '''The player can use this entity to perform an action on the given tile.

        Args:
            target: The tile to attempt to perform the action on.
            player: The player using the piece.
        '''
    

    def place(self, target:Tile, player:Player):
        '''Place this entity on the given tile.

        Args:
            target: The tile to place the entity on.
            player: The player placing the entity.
        '''
        self.game.place(self, target, player)
    

    def capture(self, target:Tile, player:Player):
        '''Capture the entity at the given tile.

        Args:
            target: The tile to capture the entity on.
            player: The player using the entity to capture the target.
        '''
        self.game.capture(self, target, player)
    

    def move(self, target:Tile, player:Player):
        '''Move this entity to the given tile.

        Args:
            target: The tile to move the entity to.
            player: The player moving the entity.
        '''
        self.game.move(self, target, player)
    

    def get_tiles_by_action(self, action_name:str) -> list[Tile]:
        '''Get the tiles that can be used with the given action.

        Args:
            action_name: The name of the action to get the tiles for.
        '''
        tiles = []
        for tile in self.game.board.values():
            actions = self.actions(tile, self.owner)
            if action_name in actions:
                if actions[action_name].can_use:
                    tiles.append(tile)
        return tiles


class Action():
    '''An action that can be performed by a piece.

    Args:
        name: The name of the action.
        description: The description of the action.
    '''
    def __init__(self, name:str, description:str, action:Callable[[Tile, Player], None], can_use:BoolWithReason):
        self.name = name
        self.description = description
        self.execute = action
        self.can_use = can_use


class ActionList(dict[str, Action]):
    '''A collection of actions that can be performed by a piece.

    Args:
        actions: The actions to add to the list.
    '''
    @overload
    def add(self, name:str, description:str, action:Callable[[Tile, Player], None], can_use:BoolWithReason):
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
            if action.can_use:
                usable[name] = action
        return usable


class Piece(Entity):
    '''The primary moveable entity in the game.
    '''


class Bird(Piece):
    abbreviation = "🐦"

    def actions(self, target:Tile, player:Player) -> ActionList:
        res = ActionList()
        res.add("move", "Move in a straight line", self.move, self.can_move(target, player))
        res.add("capture", "Capture a piece", self.capture, self.can_capture(target, player))
        res.add("place", "Place a Bird", self.place, self.game.can_place(self, target, player))
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
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        res = ActionList()
        res.add("move", "Move one square", self.move, self.can_move(target, player))
        res.add("capture", "Capture a piece", self.capture, self.can_capture(target, player))
        res.add("place", "Place a Knight", self.place, self.game.can_place(self, target, player))
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

    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList()


class Rabbit(Piece):
    abbreviation = "🐇"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList()


class Builder(Piece):
    abbreviation = "🙎"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList()


class Bomber(Piece):
    abbreviation = "💣"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList()


class Necromancer(Piece):
    abbreviation = "🧙‍♂️"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList()


class Assassin(Piece):
    abbreviation = "🗡️"
    
    def actions(self, target:Tile, player:Player) -> ActionList:
        return ActionList()


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
    color = "#fceecf"
    layer = Layer.TERRAIN


    def actions(self, target:Tile, player:Player) -> ActionList:
        res = ActionList()
        res.add("place", "Place a land tile", self.place, self.can_place(target, player))
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

    def actions(self, target:Tile, player:Player) -> ActionList:
        res = ActionList()
        res.add("place", "Place a Citadel", self.place, self.game.can_place(self, target, player))

        return res