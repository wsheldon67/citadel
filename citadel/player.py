from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict, Type
from .util import BoolWithReason, ActionError, Coordinate
from .piece import Piece

if TYPE_CHECKING:
    from .game import Game
    from .entity import Entity, EntityList
    from .piece import Piece, Citadel, Land
    from .board import Tile


class Player():
    '''A player in the game.
    '''
    def __init__(self, name:str, game:Game, color:tuple):
        '''
        Args:
            game: The game this player is in.
        '''
        from .entity import EntityList
        self.name:str = name
        self.personal_stash:EntityList['Piece'] = EntityList(game, name=f"{name}'s Personal Stash")
        self.game:Game = game
        self.rotation:int = 0
        self.color = color
    

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
            'color': self.color,
            }
    

    @classmethod
    def from_json(cls, json_data:dict, game:Game) -> 'Player':
        '''Load the player from JSON.

        Args:
            json_data: The JSON data to load.
            game: The game this player is in.
        '''
        from .entity import EntityList
        player = cls(json_data['name'], game, tuple(json_data['color']))
        player.personal_stash = EntityList.from_json(json_data['personal_stash'], game)
        player.rotation = json_data['rotation']
        return player


    def copy(self) -> 'Player':
        '''Create a copy of the player.

        Returns:
            A copy of the player.
        '''
        new_player = Player(self.name, self.game)
        new_player.personal_stash = self.personal_stash.copy()
        new_player.rotation = self.rotation
        return new_player

    
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
        from .entity import EntityList
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
        from .piece import Citadel
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
        from .board import Tile
        from .entity import Entity
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
        from .board import Tile
        from .entity import Entity
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
        from .board import Tile
        from .entity import Entity
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
        
        return actions[action_name].can_use(target, self)
    

    def perform_action(self,
        entity:'Entity'|Type['Entity']|Coordinate|Tile,
        action_name:str,
        target:Coordinate|Tile|Entity
        ):
        '''Perform an action on an entity.

        Args:
            entity: The entity to perform the action on.
            action_name: The name of the action to perform.
            target: The target of the action. This can be a coordinate, tile, or entity.
        '''
        target = self._to_tile(target)
        entity = self._to_entity(entity)
        
        if self.game.validate_actions:
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