from __future__ import annotations
from typing import NamedTuple, Iterator, Generic, TypeVar, Literal, overload, Type, TypeAlias


BoolWithReason:TypeAlias = tuple[Literal[True], None]|tuple[Literal[False], str]

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


    @property
    def current_player(self) -> 'Player':
        '''The player whose turn it is.
        '''
        return self.players[self.turn % len(self.players)]
    

    def end_turn(self):
        '''End the current player's turn.
        '''
        self.turn += 1
    

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
    def community_pieces(self) -> 'EntityList[Piece]':
        '''The pieces in the community pool that this player created.
        '''
        return [piece for piece in self.game.community_pool if piece.created_by == self]


    @property
    def is_done_choosing_personal_pieces(self) -> bool:
        '''True if the player has chosen all of their personal pieces.
        '''
        return len(self.personal_stash) >= self.game.personal_pieces_per_player

    @property
    def is_done_choosing_community_pieces(self) -> bool:
        '''True if the player has chosen all of their community pieces.
        '''
        return len(self.community_pieces) >= self.game.community_pieces_per_player


    @property
    def is_done_choosing_pieces(self) -> bool:
        '''True if the player has chosen all of their pieces.
        '''
        return self.is_done_choosing_personal_pieces and self.is_done_choosing_community_pieces


    def choose_community_piece(self, piece:'Piece'):
        '''Choose a piece for the community pool.
        '''
        if self.is_done_choosing_community_pieces:
            raise ValueError(f"Players are not allowed to choose more than {self.game.community_pieces_per_player} pieces for the community pool. '{self.name}' has already chosen {len(self.community_pieces)} community pieces.")
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
        player_lands = []
        for tile in self.game.board.values():
            if tile.land and tile.land.created_by == self:
                player_lands.append(tile.land)
    

    @property
    def is_done_placing_lands(self) -> bool:
        '''True if the player has placed all of their lands.
        '''
        return len(self.land_tiles) >= self.game.lands_per_player
        
        

    def place_land(self, coordinate:Coordinate):
        '''Place a land tile on the board.

        Args:
            coordinate: The coordinate to place the land at.
        '''
        if self.is_done_placing_lands:
            raise ValueError(f"Players are not allowed to place more than {self.game.lands_per_player} lands. Player '{self.name}' has already placed {len(self.land_tiles)} lands.")
        can_place, reason = self.game.board.can_place_land(coordinate)
        if not can_place:
            raise ValueError(f"Cannot place land at {coordinate}: {reason}")
        land = Land()
        land.created_by = self
        self.game.board.place_entity(land, coordinate)


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
            return [super().get(coord, Tile(self, coord)) for coord in coordinate]
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
    

    def place_entity(self, entity:'Entity', coordinate:Coordinate):
        '''Place an entity on the board.

        Args:
            entity: The entity to place.
            coordinate: The coordinate to place the entity at.
        '''
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
    

    def move_entity(self, entity:'Entity', to:Coordinate):
        '''Move an entity from one coordinate to another.

        Args:
            entity: The entity to move.
            to: The coordinate to move the entity to.
        '''
        from_coordinate = self.get_coordinate_of_entity(entity)
        self.remove_entity(entity, from_coordinate)
        self.place_entity(entity, to)
    

    def find_entities_by_type(self, entity_type:Type['Entity']) -> list['Entity']:
        '''Find all entities of a given type on the board.

        Args:
            entity_type: The type of entity to find.
        '''
        entities = []
        for tile in self.values():
            entities.extend([entity for entity in tile if isinstance(entity, entity_type)])
        return entities
    

    def find_tiles_by_entity_type(self, entity_type:Type['Entity']) -> list['Tile']:
        '''Find all tiles with a given entity type on the board.

        Args:
            entity_type: The type of entity to find.
        '''
        tiles = []
        for tile in self.values():
            if tile.has_type(entity_type):
                tiles.append(tile)
        return tiles


    def can_place_land(self, coordinate:Coordinate) -> BoolWithReason:
        '''Check if a land can be placed at the given coordinate.

        Args:
            coordinate: The coordinate to check.
        
        Returns:
            A tuple of (can_place, reason).
        '''
        # Can only place land on empty (water) tiles
        if self[coordinate].has_entities:
            return False, f"already occupied"
        # Land tiles must be placed adjacent (orthogonally or diagonally) to another land tile
        adjacent_to_land = any([tile.has_type(Land) for tile in self[coordinate].get_adjacent_tiles()])
        board_has_land = len(self.find_entities_by_type(Land)) > 0
        if not adjacent_to_land and board_has_land:
            return False, f"not adjacent to any land tiles"
        return True, None
    

    @property
    def citadels(self) -> 'EntityList[Citadel]':
        '''The citadels on the board.
        '''
        return self.find_entities_by_type(Citadel)


    @property
    def citadels_are_connected(self) -> bool:
        '''True if all citadels are connected to each other by a series of land tiles.
        
        Diagonals do no count, but Turtles do. This value is also True if there are not at least 2 citadels on the board.
        '''
        if len(self.citadels) <= 1:
            return True
        starting_citadel = self.find_tiles_by_entity_type(Citadel)[0]
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
            if tile.has_type(Land) or tile.has_type(Turtle):
                for adjacent_tile in tile.get_adjacent_tiles():
                    walk(adjacent_tile)
        walk(starting_citadel)
        return len(connected_citadels) == len(self.citadels)
    

    def can_move_entity(self, entity:'Entity', to:Coordinate) -> BoolWithReason:
        '''Check if an entity can be moved to the given coordinate.

        Args:
            entity: The entity to move.
            to: The coordinate to move the entity to.
        
        Returns:
            A tuple of (can_move, reason).
        '''
        new_board = self.copy()
        new_board.move_entity(entity, to)
        
        if not new_board.citadels_are_connected:
            return False, "move would disconnect citadels"
        
        return True, None



T = TypeVar('T', bound='Entity')

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
    pass

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


class Citadel(Entity):
    '''A citadel. Citadels spawn pieces. Capturing a citadel is the primary goal of the game.
    '''