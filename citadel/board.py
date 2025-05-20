from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict, overload, Type, TypeVar
import importlib

from .util import Coordinate, Rectangle, BoolWithReason, Layer
from .entity import EntityList

if TYPE_CHECKING:
    from .entity import Entity
    from .piece import Piece, Land, Citadel
    from .game import Game
    from .player import Player
    T = TypeVar('T', bound=Entity)


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
        piece_module = importlib.import_module('.piece', package='citadel')
        for entity_data in json_data['entities']:
            entity_type = entity_data['type']
            created_by = next((player for player in self.game.players if player.name == entity_data['created_by']), None)
            owner = next((player for player in self.game.players if player.name == entity_data['owner']), None)
            entity = getattr(piece_module, entity_type)(self, created_by, owner)
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
            return BoolWithReason(f"layer {entity.layer.name} already occupied by {self.get_by_layer(entity.layer)}")
        
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
        from .piece import Land
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
        from .piece import Citadel
        for entity in self:
            if isinstance(entity, Citadel):
                return entity
        return None


    @property
    def is_water(self) -> bool:
        '''True if the tile is water.'''
        from .piece import Land
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
    def __getitem__(self, coordinate:Coordinate|tuple[int, int]) -> 'Tile':
        '''Get the tile at the given coordinate.

        Args:
            coordinate: The coordinate to get the tile at.
        '''
    @overload
    def __getitem__(self, coordinates:list[Coordinate|tuple[int, int]]) -> list['Tile']:
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
        from .piece import Citadel
        return self.where(Citadel)


    @property
    def citadels_are_connected(self) -> bool:
        '''True if all citadels are connected to each other by a series of land tiles.
        
        Diagonals do no count, but Turtles do. This value is also True if there are not at least 2 citadels on the board.
        '''
        if len(self.citadels) <= 1:
            return True
        from .piece import Citadel
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

        return Rectangle(min_x or 0, max_x or 0, min_y or 0, max_y or 0)
    

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
    

    def get_equivalent_entity(self, entity:T) -> T|None:
        '''Get the equivalent entity on the board.

        The equivalent entity is an entity of the same type, coordinate, and owner.

        Args:
            entity: The entity to get the equivalent of.
        '''

        for tile in self.values():
            if tile.get_equivalent_entity(entity):
                return tile.get_equivalent_entity(entity)
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