from __future__ import annotations
import json
from typing import TypedDict, TypeVar, TYPE_CHECKING
from .util import BoolWithReason, PlacementError, GamePhase

if TYPE_CHECKING:
        from .player import Player
        from .piece import Piece, Citadel, Land
        from .board import Board, Tile
        from .entity import Entity, EntityList

class Game():
    '''The whole game.
    '''
    _player_rotations = [90, 270, 0, 180]
    _player_colors = [
        (255, 0, 0), (0, 0, 255), (0, 255, 0),
        (200, 200, 0), (200, 0, 200), (0, 200, 200),
        ]
    def __init__(self, number_of_players:int=2, lands_per_player:int=5, personal_pieces_per_player:int=3, community_pieces_per_player:int=3):
        '''Create a new game.

        Args:
            number_of_players: The number of players in the game.
            lands_per_player: The number of lands per player.
            personal_pieces_per_player: The number of personal pieces each player starts with.
            community_pieces_per_player: The number of community pieces each player may choose.
        '''
        from .board import Board
        from .player import Player
        from .entity import EntityList
        from .piece import Land, Citadel, Bird, Knight
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
        #: If true, skip validation checks.
        self.validate_actions = True
        #: The pieces available to choose from during the PIECE_SELECTION phase.
        self.available_pieces:EntityList[Piece] = EntityList(self, name='Available Pieces')
        self.available_pieces.append(Bird(self.available_pieces))
        self.available_pieces.append(Knight(self.available_pieces))
        

        for i in range(number_of_players):
            new_player = Player(f"Player {i}", self, self._player_colors[i])
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
        from . import Board, Player, EntityList
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


    def copy(self) -> 'Game':
        '''Create a copy of the game.

        Returns:
            A copy of the game.
        '''
        return self.from_json(json.loads(json.dumps(self.to_json())))


    E = TypeVar('E')

    def get_equivalent(self, obj:E) -> E|None:
        '''Get the equivalent object from the Game.

        When a game is copied, this method can be used to get an object represented in the original.
        '''
        from . import Player, Entity, Tile
        if isinstance(obj, Player):
            for player in self.players:
                if player.name == obj.name:
                    return player
        elif isinstance(obj, Entity):
            in_board = self.board.get_equivalent_entity(obj)
            if in_board:
                return in_board
            in_pool = self.community_pool.get_equivalent_entity(obj)
            if in_pool:
                return in_pool
            in_graveyard = self.graveyard.get_equivalent_entity(obj)
            if in_graveyard:
                return in_graveyard
            for player in self.players:
                in_personal_stash = player.personal_stash.get_equivalent_entity(obj)
                if in_personal_stash:
                    return in_personal_stash
        elif isinstance(obj, Tile):
            return self.board[obj.coordinate]
        else:
            raise TypeError(f"Object must be a Player or Entity, not {type(obj)}.")


    @property
    def current_player(self) -> Player:
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
        from .util import GamePhase
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
    

    def can_move(self, piece:Piece, target:Tile, player:Player) -> BoolWithReason:
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

        new_game = piece.simulate('move', target, player)
        
        if not new_game.board.citadels_are_connected:
            return BoolWithReason(f"moving {piece} to {target} would disconnect citadels")

        return BoolWithReason(True)


    def move(self, piece:'Piece', target:'Tile', player:'Player'):
        '''Move a piece to the given tile.

        Args:
            piece: The piece to move.
            target: The tile to move the piece to.
            player: The player moving the piece.
        '''
        if self.validate_actions:
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
        from .piece import Piece
        can_add_to_tile = self.board[target.coordinate].can_add(entity)
        if not can_add_to_tile:
            return BoolWithReason(f"cannot add {entity} to {target}: {can_add_to_tile.reason}")
    
        if not entity in player.placeable_entities:
            return BoolWithReason(f"Player '{player}' does not have access to place {entity}.")
    
        if isinstance(entity, Piece) and not player.is_adjacent_to_citadel(target):
            return BoolWithReason(f"Cannot place {entity} at {target}: not adjacent to any of player's citadels.")

        return BoolWithReason(True)


    def place(self, entity:'Entity', target:'Tile', player:'Player'):
        '''Place an entity on the given tile.

        Args:
            entity: The entity to place.
            target: The tile to place the entity on.
        '''
        from .entity import Entity
        if not isinstance(entity, Entity):
            raise TypeError(f"Can only place an Entity, not {type(entity)}.")
        if self.validate_actions:
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
        from .piece import Piece
        if not target.where(Piece):
            return BoolWithReason(f"{target} has no pieces to capture.")
        
        new_game = entity.simulate('capture', target, player)
        if not new_game.board.citadels_are_connected:
            return BoolWithReason(f"capture at {target} would disconnect citadels")

        return BoolWithReason(True)
    

    def capture(self, entity:Entity, target:Tile, player:Player):
        '''Capture an entity, sending it to the graveyard.'''
        from .piece import Piece
        if self.validate_actions:
            can_capture = self.can_capture(entity, target, player)
            if not can_capture:
                raise PlacementError(f"Cannot capture {target} with {entity}: {can_capture.reason}")
        entity = target.where(Piece)[0]
        self.graveyard.append(entity)
        self.board.remove(entity)
