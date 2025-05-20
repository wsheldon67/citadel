from __future__ import annotations
from typing import Generic, TypeVar, TypedDict, Iterator, TYPE_CHECKING, Type
from abc import abstractmethod, ABC
from .util import BoolWithReason, Layer, Coordinate
import importlib


if TYPE_CHECKING:
    from .player import Player
    from .game import Game
    from .board import Board, Tile, Vector
    from .piece import ActionList


class Entity(ABC):
    '''An game object that can be placed on a tile.

    Args:
        created_by: The player who created this entity.
        owner: The player who owns this entity.
        location: The EntityList this entity is in.
    '''
    layer:Layer = Layer.PIECE
    abbreviation:str = " "
    img:str = ""

    def __init__(self, location:EntityList, created_by:Player|None=None, owner:Player|None=None):
        self.created_by:Player|None = created_by
        self.owner:Player|None = owner
        self.location:EntityList = location
        self.game:Game = location.game
    

    @property
    def color(self) -> tuple:
        if self.owner:
            return self.owner.color
        return (255, 255, 255)


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
        return self.__class__(self.location, self.created_by, self.owner)


    @property
    def board(self) -> Board|None:
        '''The board this entity is on.
        '''
        if not self.location:
            return None
        from .board import Tile
        if isinstance(self.location, Tile):
            return self.location.board
    

    @property
    def coordinate(self) -> Coordinate|None:
        '''The coordinate of this piece on the board.
        '''
        if not self.location:
            return None
        from .board import Tile
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
    

    def can_place(self, target:Tile, player:Player) -> BoolWithReason:
        return self.game.can_place(self, target, player)
    

    def get_tiles_by_action(self, action_name:str) -> list[Tile]:
        '''Get the tiles that can be used with the given action.

        Args:
            action_name: The name of the action to get the tiles for.
        '''
        tiles = []
        for tile in self.game.board.values():
            actions = self.actions(tile, self.owner)
            if action_name in actions:
                if actions[action_name].can_use(tile, self.owner):
                    tiles.append(tile)
        return tiles
    

    def simulate(self, action:str, target:Tile, player:Player) -> Game:
        '''Simulate an action on this entity.

        Args:
            action: The name of the action to simulate.
            target: The tile to simulate the action on.
            player: The player using the entity to perform the action.
        
        Returns:
            A copy of the game with the action performed.
        '''
        game = self.game.copy()
        game.validate_actions = False
        new_player = game.get_equivalent(player)
        new_target = game.get_equivalent(target)
        entity = game.get_equivalent(self)
        entity.actions(new_target, new_player)[action].execute(new_target, new_player)
        return game
    

T = TypeVar('T', bound='Entity')
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
        piece_module = importlib.import_module('.piece', package='citadel')
        for entity_data in json_data['entities']:
            entity_type = entity_data['type']
            created_by = next((player for player in game.players if player.name == entity_data['created_by']), None)
            owner = next((player for player in game.players if player.name == entity_data['owner']), None)
            entity = getattr(piece_module, entity_type)(self, created_by, owner)
            entities.append(entity)
        self.extend(entities)
        return self
    

    def copy(self) -> 'EntityList':
        '''Create a copy of the entity list.

        Returns:
            A copy of the entity list.
        '''
        new_list = EntityList(self.game, name=self.name)
        for entity in self:
            new_list.append(entity.copy())
        return new_list


    def get_equivalent_entity(self, entity:T) -> T|None:
        '''Get the equivalent entity in the list.

        The equivalent entity is an entity of the same type, coordinate, and owner.

        Args:
            entity: The entity to get the equivalent of.
        '''
        for e in self:
            if isinstance(e, type(entity)) and e.coordinate == entity.coordinate and e.owner.name == entity.owner.name:
                return e
        return None


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