from __future__ import annotations
from typing import NamedTuple, Iterator, Generic, TypeVar, Literal, overload, Type, TypeAlias
from enum import Enum


class BoolWithReason(str):
    '''A string that can be used as a boolean with a reason.
    '''
    def __bool__(self) -> bool:
        return len(self) == 0


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
        self.community_pool:EntityList[Piece] = EntityList()
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

    

class Player():
    '''A player in the game.
    '''
    def __init__(self, name:str, game:Game):
        '''
        Args:
            game: The game this player is in.
        '''
        self.personal_stash:EntityList['Piece'] = EntityList()
        self.game:Game = game
        self.name:str = name


    def can_use_piece(self, piece:'Piece') -> bool:
        '''Check if a piece can be used by this player.
        '''
        return piece in self.personal_stash or piece in self.game.community_pool
    

    @property
    def community_entities(self) -> 'EntityList[Piece]':
        '''The pieces in the community pool that this player created.
        '''
        return [entity for entity in self.game.community_pool if entity.created_by == self]


    @property
    def is_done_choosing_personal_pieces(self) -> bool:
        '''True if the player has chosen all of their personal pieces.
        '''
        personal_pieces = self.personal_stash.get_by_type(Piece)
        return len(personal_pieces) >= self.game.personal_pieces_per_player


    @property
    def is_done_choosing_community_pieces(self) -> bool:
        '''True if the player has chosen all of their community pieces.
        '''
        community_pieces = self.community_entities.get_by_type(Piece)
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
        return self.game.board.find_entities(Citadel, self)


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
        return BoolWithReason("")
        

    def place_land(self, coordinate:Coordinate):
        '''Place a land tile on the board.

        Args:
            coordinate: The coordinate to place the land at.
        '''
        can_place = self.can_place_land(coordinate)
        if not can_place:
            raise PlacementError(f"Cannot place land at {coordinate}: {can_place}")
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
        return BoolWithReason("")
        
    

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


class Board(dict[Coordinate, 'Tile']):
    '''A collection of tiles.
    '''

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
    

    def place_entity(self, entity:'Entity', coordinate:Coordinate, check:bool=True):
        '''Place an entity on the board.

        Args:
            entity: The entity to place.
            coordinate: The coordinate to place the entity at.
            check: If True, check if the placement is valid.
        '''
        if check and not self.can_place_entity(entity, coordinate):
            raise PlacementError(f"Cannot place {entity} at {coordinate}: {self.can_place_entity(entity, coordinate)}")
        if coordinate not in self:
            self[coordinate] = Tile(self, coordinate)
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
    

    def move_entity(self, entity:'Entity', to:Coordinate, check:bool=True):
        '''Move an entity from one coordinate to another.

        Args:
            entity: The entity to move.
            to: The coordinate to move the entity to.
            check: If True, check if the move is valid.
        '''
        if check and not self.can_move_piece(entity, to):
            raise PlacementError(f"Cannot move {entity} to {to}: {self.can_move_entity(entity, to)}")
        from_coordinate = self.get_coordinate_of_entity(entity)
        self.remove_entity(entity, from_coordinate)
        self.place_entity(entity, to)
    

    def find_entities(self,
        entity_type:Type[T]=Type['Entity'],
        created_by:Player|None=None,
        layer:Layer|None=None) -> 'EntityList[T]':
        '''Search for entities on the board.

        If any arguments are not provided, all entities for that parameter are returned.
        
        Args:
            entity_type: The type of entity to find.
            created_by: The player who created the entity.
            layer: The layer of the entity.
        '''
        entities = EntityList()
        for tile in self.values():
            for entity in tile:
                if not isinstance(entity, entity_type):
                    continue
                if created_by and entity.created_by != created_by:
                    continue
                if layer and entity.layer != layer:
                    continue
                entities.append(entity)
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
        board_has_land = len(self.find_entities(Land)) > 0
        if not adjacent_to_land and board_has_land:
            return BoolWithReason(f"not adjacent to any land tiles")
        return BoolWithReason("")
    

    @property
    def citadels(self) -> 'EntityList[Citadel]':
        '''The citadels on the board.
        '''
        return self.find_entities(Citadel)


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
        return BoolWithReason("")


    def can_place_entity(self, entity:'Entity', coordinate:Coordinate) -> BoolWithReason:
        '''Check if an entity can be placed at the given coordinate.

        Args:
            entity: The entity to place.
            coordinate: The coordinate to place the entity at.
        '''
        can_add = self[coordinate].can_add(entity)
        if not can_add:
            return BoolWithReason(f"cannot add {entity.__class__.__name__} to tile at {coordinate}: {can_add}")
        
        if isinstance(entity, Citadel) and not self._can_place_citadel(coordinate):
            return self._can_place_citadel(coordinate)
        if isinstance(entity, Land) and not self._can_place_land(coordinate):
            return self._can_place_land(coordinate)
        
        new_board = self.copy()
        new_board.place_entity(entity, coordinate, check=False)

        if not new_board.citadels_are_connected:
            return BoolWithReason("placement would disconnect citadels")
        
        return BoolWithReason("")
    

    def can_move_piece(self, piece:'Piece', to:Coordinate) -> BoolWithReason:
        '''Check if an entity can be moved to the given coordinate.

        Args:
            piece: The piece to move.
            to: The coordinate to move the entity to.
        '''
        if not self[to].can_add(piece):
            return self[to].can_add(piece)

        new_board = self.copy()
        new_board.move_entity(piece, to, check=False)
        
        if not new_board.citadels_are_connected:
            return BoolWithReason("move would disconnect citadels")

        return BoolWithReason("")


    @property
    def extents(self) -> Rectangle:
        '''The extents of the board. The extents are the minimum and maximum x and y coordinates of the tiles on the board.
        '''
        min_x = min_y = -1e9
        max_x = max_y = 1e9
        for coordinate in self.keys():
            if coordinate.x < min_x:
                min_x = coordinate.x
            if coordinate.x > max_x:
                max_x = coordinate.x
            if coordinate.y < min_y:
                min_y = coordinate.y
            if coordinate.y > max_y:
                max_y = coordinate.y
        return Rectangle(min_x, max_x, min_y, max_y)


class EntityList(list, Generic[T]):
    '''A collection of entities.
    '''

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
    

    def get_by_type(self, entity_type: Type[T]) -> 'EntityList[T]':
        '''Get all entities of the given type.

        Args:
            entity_type: The type of entity to get.
        '''
        return EntityList([entity for entity in self if isinstance(entity, entity_type)])
    

    def pop_by_type(self, entity_type: Type[T]) -> T:
        '''Pull the first entity of the given type out of this entity list.

        Args:
            entity_type: The type of entity to pop.
        '''
        for i, entity in enumerate(self):
            if isinstance(entity, entity_type):
                return self.pop(i)
        raise ValueError(f"No {entity_type.__name__} found in list")


class Tile(EntityList):
    '''A single tile (location) on the board.
    '''
    def __init__(self, board:Board, coordinate:Coordinate):
        '''Create a new tile.

        Args:
            board: The board this tile is on.
            coordinate: The coordinate of this tile.
        '''
        super().__init__()
        self.board = board
        self.coordinate = coordinate
    

    def append(self, entity:Entity):
        can_add = self.can_add(entity)
        if can_add:
            super().append(entity)
        else:
            raise ValueError(f"Cannot add {entity.__class__.__name__} to tile at {self.coordinate}: {can_add}")
    

    def can_add(self, entity:Entity) -> BoolWithReason:
        '''Check if an entity can be added to this tile.

        Args:
            entity: The entity to add.
        '''
        if self.get_by_layer(entity.layer):
            return BoolWithReason(f"layer {entity.layer.name} already occupied")
        
        if entity.layer.value > 0:
            layer_below = Layer(entity.layer.value - 1)
            if not self.get_by_layer(layer_below):
                return BoolWithReason(f"{entity.layer.name}-layer entities must be placed on top of a {layer_below.name}-layer entity")
    
        return BoolWithReason("")
    
    

    def get_by_layer(self, layer:Layer) -> 'Entity':
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



class Entity():
    '''An game object that can be placed on a tile.
    '''
    layer:Layer = Layer.PIECE
    def __init__(self):
        self.created_by:Player|None = None


class Piece(Entity):
    '''The primary moveable entity in the game.
    '''


class Bird(Piece):
    pass


class Knight(Piece):
    pass


class Turtle(Piece):
    layer = Layer.TERRAIN


class Rabbit(Piece):
    pass


class Builder(Piece):
    pass


class Bomber(Piece):
    pass


class Necromancer(Piece):
    pass


class Assassin(Piece):
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
    layer = Layer.TERRAIN


class Citadel(Entity):
    '''A citadel. Citadels spawn pieces. Capturing a citadel is the primary goal of the game.
    '''