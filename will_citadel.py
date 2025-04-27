from __future__ import annotations
from typing import NamedTuple, Iterator, Generic, TypeVar, Literal, overload, Type, TypeAlias
from enum import Enum


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


class PlacementError(Exception):
    pass


class GamePhase(Enum):
    '''The phase of the game.'''
    PIECE_SELECTION = 0
    LAND_PLACEMENT = 1
    CITADEL_PLACEMENT = 2
    BATTLE = 3
    END = 4


class Coordinate(NamedTuple):
    '''A coordinate on the board.'''
    x: int
    y: int

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
    def __init__(self, number_of_players:int=2, lands_per_player:int=5, personal_pieces_per_player:int=3, community_pieces_per_player:int=3):
        '''Create a new game.

        Args:
            number_of_players: The number of players in the game.
            lands_per_player: The number of lands per player.
            personal_pieces_per_player: The number of personal pieces each player starts with.
            community_pieces_per_player: The number of community pieces each player may choose.
        '''
        self.lands_per_player:int = lands_per_player
        self.personal_pieces_per_player:int = personal_pieces_per_player
        self.community_pieces_per_player:int = community_pieces_per_player
        self.players:list[Player] = [Player(f"Player {i}", self) for i in range(number_of_players)]
        self.board = Board()
        self.turn:int = 0
        self.community_pool:EntityList[Piece] = EntityList(name='Community Pool')
        self.graveyard:EntityList[Piece] = EntityList(name='Graveyard')
        self.citadels_per_player:int = 1

        for i in range(self.lands_per_player):
            for player in self.players:
                land = Land()
                land.created_by = player
                player.personal_stash.append(land)
        for i in range(self.citadels_per_player):
            for player in self.players:
                citadel = Citadel()
                citadel.created_by = player
                player.personal_stash.append(citadel)


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
        if not all([player.is_done_choosing_pieces for player in self.players]):
            return GamePhase.PIECE_SELECTION
        if not all([player.is_done_placing_lands for player in self.players]):
            return GamePhase.LAND_PLACEMENT
        if not all([player.is_done_placing_citadels for player in self.players]):
            return GamePhase.CITADEL_PLACEMENT
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

    

class Player():
    '''A player in the game.
    '''
    def __init__(self, name:str, game:Game):
        '''
        Args:
            game: The game this player is in.
        '''
        self.personal_stash:EntityList['Piece'] = EntityList(name=f"{name}'s Personal Stash")
        self.game:Game = game
        self.name:str = name

    
    @property
    def place_from_lists(self) -> list[EntityList]:
        '''The entity lists this player can place from.
        '''
        return [self.personal_stash, self.game.community_pool]


    def can_place_entity(self, entity:'Entity') -> BoolWithReason:
        '''Check if an entity can be used by this player.
        '''
        if any([entity in entity_list for entity_list in self.place_from_lists]):
            return BoolWithReason(True)
        return BoolWithReason(f"Player '{self.name}' does not have access to {entity}.")


    def remove_placeable_entity(self, entity:'Entity'):
        '''Remove an entity out of the entities available to this player for placement.
        '''
        for entity_list in self.place_from_lists:
            if entity in entity_list:
                entity_list.remove(entity)
                return
        raise ValueError(f"Entity '{entity}' not found in '{self.name}'s placeable entities.")
    

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


    def choose_community_piece(self, piece:'Piece'):
        '''Choose a piece for the community pool.
        '''
        if self.is_done_choosing_community_pieces:
            raise ValueError(f"Players are not allowed to choose more than {self.game.community_pieces_per_player} pieces for the community pool. '{self.name}' has already chosen {len(self.community_entities)} community pieces.")
        piece.created_by = self
        self.game.community_pool.append(piece)

    
    def choose_personal_piece(self, piece:'Piece'):
        '''Choose a piece for the personal stash.
        '''
        if self.is_done_choosing_personal_pieces:
            raise ValueError(f"Players are not allowed to choose more than {self.game.personal_pieces_per_player} pieces for their personal stash. '{self.name}' has already chosen {len(self.personal_stash)} personal pieces.")
        piece.created_by = self
        self.personal_stash.append(piece)


    @property
    def land_tiles(self) -> 'EntityList[Land]':
        '''The land tiles this player has placed.
        '''
        player_lands = EntityList()
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
        return self.game.board.where(Citadel, self)


    def can_place_land(self, coordinate:Coordinate) -> BoolWithReason:
        '''Check if a land can be placed at the given coordinate.

        Args:
            coordinate: The coordinate to check.
        '''
        if self.is_done_placing_lands:
            return BoolWithReason(f"Players are not allowed to place more than {self.game.lands_per_player} lands. Player '{self.name}' has already placed {len(self.land_tiles)} lands.")
        can_place = self.game.board.can_place_entity(Land(), coordinate)
        if not can_place:
            return can_place
        return BoolWithReason(True)
        

    def place_land(self, coordinate:Coordinate):
        '''Place a land tile on the board.

        Args:
            coordinate: The coordinate to place the land at.
        '''
        can_place = self.can_place_land(coordinate)
        if not can_place:
            raise PlacementError(f"Cannot place land at {coordinate}: {can_place.reason}")
        land = self.personal_stash.pop_by_type(Land)
        self.game.board.place_entity(land, coordinate)
        self.game.end_turn()

    
    @property
    def is_done_placing_citadels(self) -> bool:
        '''True if the player has placed all of their citadels.
        '''
        return len(self.citadels) >= self.game.citadels_per_player
    

    def can_place_citadel(self, coordinate:Coordinate) -> BoolWithReason:
        '''Check if a citadel can be placed at the given coordinate.

        Args:
            coordinate: The coordinate to check.
        '''
        if self.is_done_placing_citadels:
            return BoolWithReason(f"Players are not allowed to place more than {self.game.citadels_per_player} citadels. Player '{self.name}' has already placed {len(self.citadels)} citadels.")
        can_place = self.game.board.can_place_entity(Citadel(), coordinate)
        if not can_place:
            return can_place
        return BoolWithReason(True)
    

    def place_citadel(self, coordinate:Coordinate):
        '''Place a citadel on the board.
        Args:
            coordinate: The coordinate to place the citadel at.
        '''
        can_place = self.can_place_citadel(coordinate)
        if not can_place:
            raise PlacementError(f"Cannot place citadel at {coordinate}: {can_place}")
        citadel = self.personal_stash.pop_by_type(Citadel)
        self.game.board.place_entity(citadel, coordinate)
        self.game.end_turn()

    
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
    
    
    def can_place_piece(self, piece:'Piece', coordinate:Coordinate) -> BoolWithReason:
        '''Check if a piece can be placed at the given coordinate.

        Args:
            piece: The piece to place.
            coordinate: The coordinate to place the piece at.
        '''
        # Check if the player has access to the piece
        if not self.can_place_entity(piece):
            return BoolWithReason(f"Player '{self.name}' does not have access to {piece.__class__.__name__}.")
        
        # Check tile & board-level constraints.
        can_place = self.game.board.can_place_entity(piece, coordinate)
        if not can_place:
            return can_place
        
        # Must place adjacent to their own Citadel
        if not self.is_adjacent_to_citadel(coordinate):
            return BoolWithReason(f"Cannot place {piece.__class__.__name__} at {coordinate}: not adjacent to any of player's citadels.")
        
        return BoolWithReason(True)
    

    def place_piece(self, piece:'Piece', coordinate:Coordinate):
        '''Place a piece on the board.

        Args:
            piece: The piece to place.
            coordinate: The coordinate to place the piece at.
        '''
        can_place = self.can_place_piece(piece, coordinate)
        if not can_place:
            raise PlacementError(f"Cannot place {piece.__class__.__name__} at {coordinate}: {can_place.reason}")
        self.game.board.place_entity(piece, coordinate)
        self.remove_placeable_entity(piece)
        self.game.end_turn()
    

    def can_move_piece(self, piece:'Piece', to:Coordinate) -> BoolWithReason:
        '''Check if a piece can be moved to the given coordinate.

        Args:
            piece: The piece to move.
            to: The coordinate to move the piece to.
        '''
        # Check tile & board-level constraints.
        can_move = self.game.board.can_move_piece(piece, to)
        if not can_move:
            return can_move
        
        # Can only move own pieces
        if piece.created_by != self:
            return BoolWithReason(f"Cannot move {piece}: not owned by player '{self.name}'.")
        
        return BoolWithReason(True)
        
    
    def move_piece(self, piece:'Piece', to:Coordinate):
        '''Move a piece to the given coordinate.

        Args:
            piece: The piece to move.
            to: The coordinate to move the piece to.
        '''
        original_coordinate = piece.location.coordinate
        can_move = self.can_move_piece(piece, to)
        assert original_coordinate == piece.location.coordinate, f"Piece {piece} moved during can_move check; original coordinate: {original_coordinate}, new coordinate: {piece.location.coordinate}"
        if not can_move:
            raise PlacementError(f"Cannot move {piece} to {to}: {can_move.reason}")
        self.game.board.move_entity(piece, to)
        self.game.end_turn()
        

    def _repr_html_(self) -> str:
        return f"""<div style='display: flex; flex-direction: column;'>{self.name}{self.personal_stash._repr_html_()}</div>"""


class Board(dict[Coordinate, 'Tile']):
    '''A collection of tiles.
    '''

    def __init__(self, name:str='main'):
        '''Create a new board.

        Args:
            name: A unique name for this board.
        '''
        super().__init__()
        self.name = name
    

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
    def __getitem__(self, coordinate):
        if isinstance(coordinate, list):
            return [self.get(coord, Tile(self, coord)) for coord in coordinate]
        elif isinstance(coordinate, Coordinate):
            return super().get(coordinate, Tile(self, coordinate))
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
        new_board = Board()
        for coordinate, tile in self.items():
            new_tile = Tile(new_board, coordinate)
            new_tile.extend(tile)
            new_board[coordinate] = new_tile
        return new_board
    

    def place_entity(self, entity:'Entity', coordinate:Coordinate, to_test:bool=False):
        '''Place an entity on the board.

        Args:
            entity: The entity to place.
            coordinate: The coordinate to place the entity at.
            to_test: If True, force the placement and do not change the entity.
        '''
        if not to_test and not self.can_place_entity(entity, coordinate):
            raise PlacementError(f"Cannot place {entity} at {coordinate}: {self.can_place_entity(entity, coordinate)}")
        if coordinate not in self:
            self[coordinate] = Tile(self, coordinate)
        if not to_test:
            entity.location = self[coordinate]
        self[coordinate].append(entity)
    

    def get_coordinate_of_entity(self, entity:'Entity') -> Coordinate|None:
        '''Get the coordinate of an entity.

        Args:
            entity: The entity to get the coordinate of.
        '''
        for coordinate, tile in self.items():
            if entity in tile:
                return coordinate
        return None
    

    def remove_entity(self, entity:'Entity') -> 'Entity':
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
    

    def move_entity(self, entity:'Entity', to:Coordinate, to_test:bool=False):
        '''Move an entity from one coordinate to another.

        Args:
            entity: The entity to move.
            to: The coordinate to move the entity to.
            to_test: If True, force the move and do not change the entity.
        '''
        if not to_test and not self.can_move_piece(entity, to):
            raise PlacementError(f"Cannot move {entity} to {to}: {self.can_move_piece(entity, to).reason}")
        self.remove_entity(entity)
        self.place_entity(entity, to, to_test)
    

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
        entities = EntityList()
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


    def _can_place_land(self, coordinate:Coordinate) -> BoolWithReason:
        '''Do not call this method directly; use can_place_entity instead.'''
        # Land tiles must be placed adjacent (orthogonally or diagonally) to another land tile
        adjacent_to_land = any([tile.has_type(Land) for tile in self[coordinate].get_adjacent_tiles()])
        board_has_land = len(self.where(Land)) > 0
        if not adjacent_to_land and board_has_land:
            return BoolWithReason(f"not adjacent to any land tiles")
        return BoolWithReason(True)
    

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
    

    def _can_place_citadel(self, coordinate:Coordinate) -> BoolWithReason:
        '''Do not call this method directly; use can_place_entity instead.'''
        return BoolWithReason(True)


    def can_place_entity(self, entity:'Entity', coordinate:Coordinate) -> BoolWithReason:
        '''Check if an entity can be placed at the given coordinate.

        Args:
            entity: The entity to place.
            coordinate: The coordinate to place the entity at.
        '''
        can_add = self[coordinate].can_add(entity)
        if not can_add:
            return BoolWithReason(f"cannot add {entity.__class__.__name__} to tile at {coordinate}: {can_add.reason}")
        
        if isinstance(entity, Citadel) and not self._can_place_citadel(coordinate):
            return self._can_place_citadel(coordinate)
        if isinstance(entity, Land) and not self._can_place_land(coordinate):
            return self._can_place_land(coordinate)
        
        new_board = self.copy()
        new_board.place_entity(entity, coordinate, to_test=True)

        if not new_board.citadels_are_connected:
            return BoolWithReason("placement would disconnect citadels")
        
        return BoolWithReason(True)
    

    def can_move_piece(self, piece:'Piece', to:Coordinate) -> BoolWithReason:
        '''Check if an entity can be moved to the given coordinate.

        Args:
            piece: The piece to move.
            to: The coordinate to move the entity to.
        '''
        if not self[to].can_add(piece):
            return self[to].can_add(piece)
        
        can_move_piece = piece.can_move_to(to)
        if not can_move_piece:
            return can_move_piece

        new_board = self.copy()
        new_board.move_entity(piece, to, to_test=True)
        
        if not new_board.citadels_are_connected:
            return BoolWithReason("move would disconnect citadels")

        return BoolWithReason(True)


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
                color, abbreviation = self[coordinate].short_html
                cells.append(f"<td style='background-color: {color}; width: 18px; height 34px; border: 1px solid white; color: black; text-align: center;'>{abbreviation}</td>")
            rows.append(f"<tr style='height: 36px;'><th>x{x}</th>{''.join(cells)}</tr>")
        return f"<table>{''.join(rows)}</table>"


class EntityList(list, Generic[T]):
    '''A collection of entities.
    '''

    def __init__(self, entities:list[T]=[], name:str|None=None):
        '''Create a new entity list.

        Args:
            entities: The entities to add to the list.
            name: A unique name for this entity list.
        '''
        super().__init__(entities)
        self.name = name

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
    

    @overload
    def where(self,
        entity_type: Type[T],
        created_by: Player|None=None,
        owner: Player|None=None,
        layer: Layer|None=None) -> 'EntityList[T]':
        pass
    @overload
    def where(self,
        entity_type:None=None,
        created_by: Player|None=None,
        owner: Player|None=None,
        layer: Layer|None=None) -> 'EntityList[Entity]':
        pass
    def where(self,
        entity_type: Type[T]|None=None,
        created_by: Player|None=None,
        owner: Player|None=None,
        layer: Layer|None=None) -> 'EntityList[T]':
        '''Search for entities in the collection.
        
        If any arguments are not provided, all entities for that parameter are returned.
        
        Args:
            entity_type: The type of entity to find.
            created_by: The player who created the entity.
            owner: The player who owns the entity.
            layer: The layer of the entity.
        '''
        entities = EntityList()
        for entity in self:
            if entity_type and not isinstance(entity, entity_type):
                continue
            if created_by and entity.created_by != created_by:
                continue
            if layer and entity.layer != layer:
                continue
            if owner and entity.owner != owner:
                continue
            entities.append(entity)
        return entities
    

    def pop_by_type(self, entity_type: Type[T]) -> T:
        '''Pull the first entity of the given type out of this entity list.

        Args:
            entity_type: The type of entity to pop.
        '''
        for i, entity in enumerate(self):
            if isinstance(entity, entity_type):
                return self.pop(i)
        raise ValueError(f"No {entity_type.__name__} found in list")
    

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
        entities = EntityList()
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
            res.append(f"<div style='background-color: {entity.color}'>{entity.abbreviation}</div>")
        return f"<div style='display: flex; flex-wrap: wrap; width: 100px;'>{''.join(res)}</div>"



class Tile(EntityList):
    '''A single tile (location) on the board.
    '''
    def __init__(self, board:Board, coordinate:Coordinate):
        '''Create a new tile.

        Args:
            board: The board this tile is on.
            coordinate: The coordinate of this tile.
        '''
        super().__init__(name=f"{board.name}{coordinate}")
        self.board = board
        self.coordinate = coordinate
    

    def __hash__(self) -> int:
        return hash((self.coordinate, self.board))


    def __eq__(self, other:object) -> bool:
        if not isinstance(other, Tile):
            return False
        return self.coordinate == other.coordinate and self.board == other.board
    

    def append(self, entity:Entity):
        can_add = self.can_add(entity)
        if can_add:
            super().append(entity)
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
    def short_html(self) -> tuple[str, str]:
        '''Return a css color representing the terrain layer, and single character representing the piece layer.
        '''
        terrain_layer = self.get_by_layer(Layer.TERRAIN)
        if terrain_layer:
            color = terrain_layer.color
        else:
            color = "#87CEEB"
        
        piece_layer = self.get_by_layer(Layer.PIECE)
        if piece_layer:
            abbreviation = piece_layer.abbreviation
        else:
            abbreviation = " "
        return color, abbreviation



class Entity():
    '''An game object that can be placed on a tile.

    Args:
        created_by: The player who created this entity.
        owner: The player who owns this entity.
        location: The EntityList this entity is in.
    '''
    layer:Layer = Layer.PIECE
    color:str = "#000000"
    abbreviation:str = " "

    def __init__(self, created_by:Player|None=None, owner:Player|None=None, location:EntityList|None=None):
        self.created_by:Player|None = created_by
        self.owner:Player|None = owner
        self.location:EntityList|None = location

    

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


class Piece(Entity):
    '''The primary moveable entity in the game.
    '''

    def can_move_to(self, to:Coordinate) -> BoolWithReason:
        '''Check if this piece can move to the given coordinate.

        This method only needs to specify piece-specific rules.

        Args:
            to: The coordinate to move to.
        '''
        if not self.location:
            return BoolWithReason(f"Piece {self} has no location.")
        if not isinstance(self.location, Tile):
            return BoolWithReason(f"Piece {self} is not on a board.")
        return BoolWithReason(True)
    

    def can_capture(self, to:Coordinate) -> BoolWithReason:
        '''Check if this piece can capture another piece at the given coordinate.

        This method only needs to specify piece-specific rules.

        Args:
            to: The coordinate to capture at.
        '''
        # cannot capture if not on a board
        if not self.location:
            return BoolWithReason(f"Piece {self} has no location.")
        if not isinstance(self.location, Tile):
            return BoolWithReason(f"Piece {self} is not on a board.")
        
        # can only capture if there is an opponent's piece on the tile.
        if not self.location.where_not(owner=self.owner).where(Piece):
            return BoolWithReason(f"Cannot capture at {to}: no opponent pieces to capture.")
        
        return BoolWithReason(True)
    

    @property
    def coordinate(self) -> Coordinate|None:
        '''The coordinate of this piece on the board.
        '''
        if not self.location:
            return None
        if not isinstance(self.location, Tile):
            return None
        return self.location.coordinate


class Bird(Piece):
    abbreviation = "🐦"

    def can_move_to(self, to:Coordinate) -> BoolWithReason:
        '''The Bird moves in a straight line, either horizontally or vertically, for as many tiles as you want. It cannot move diagonally.
        '''
        base = super().can_move_to(to)
        if not base:
            return base
        # TODO can birds fly over other pieces?
        if self.coordinate.x != to.x and self.coordinate.y != to.y:
            return BoolWithReason(f"Cannot move {self} to {to}: not in a straight line.")
        
        return BoolWithReason(True)
    

    def can_capture(self, to:Coordinate) -> BoolWithReason:
        '''The Bird can capture any piece it lands on during its move.
        '''
        base = super().can_capture(to)
        if not base:
            return base
        
        can_move = self.can_move_to(to)
        if not can_move:
            return BoolWithReason(f"{can_move.reason}; Birds can only capture pieces they can move to.")


class Knight(Piece):
    abbreviation = "♞"
    
    def can_move_to(self, to):
        '''The Knight moves one square at a time, either orthogonally (up, down, left, right) or diagonally.
        '''
        base = super().can_move_to(to)
        if not base:
            return base
        
        if to not in self.coordinate.get_adjacent_coordinates():
            return BoolWithReason(f"Cannot move {self} to {to}: not adjacent to current location.")
        return BoolWithReason(True)


    def can_capture(self, to:Coordinate) -> BoolWithReason:
        '''The Knight can capture any piece it lands on during its move.
        '''
        base = super().can_capture(to)
        if not base:
            return base
        
        can_move = self.can_move_to(to)
        if not can_move:
            return BoolWithReason(f"{can_move.reason}; Knights can only capture pieces they can move to.")


class Turtle(Piece):
    layer = Layer.TERRAIN
    abbreviation = "🐢"


class Rabbit(Piece):
    abbreviation = "🐇"
    pass


class Builder(Piece):
    abbreviation = "🙎"
    pass


class Bomber(Piece):
    abbreviation = "💣"
    pass


class Necromancer(Piece):
    abbreviation = "🧙‍♂️"
    pass


class Assassin(Piece):
    abbreviation = "🗡️"
    pass


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


class Citadel(Entity):
    '''A citadel. Citadels spawn pieces. Capturing a citadel is the primary goal of the game.
    '''
    abbreviation = "⛃"