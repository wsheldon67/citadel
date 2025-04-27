from will_citadel import Game, Coordinate
from will_citadel import Bird, Knight, Turtle, Rabbit, Builder, Bomber, Necromancer, Assassin
from will_citadel import Land
from will_citadel import PlacementError


class ExampleGame():

    def __init__(self):
        self.game = Game()
    
    def choose_personal_pieces(self) -> Game:
        player0, player1 = self.game.players
        player0.choose_personal_piece(Knight())
        player1.choose_personal_piece(Bird())
        player0.choose_personal_piece(Turtle())
        player1.choose_personal_piece(Rabbit())
        player0.choose_personal_piece(Knight())
        player1.choose_personal_piece(Bird())
        return self.game
    
    def choose_community_pieces(self) -> Game:
        player0, player1 = self.game.players
        player0.choose_community_piece(Builder())
        player1.choose_community_piece(Assassin())
        player0.choose_community_piece(Bomber())
        player1.choose_community_piece(Builder())
        player0.choose_community_piece(Necromancer())
        player1.choose_community_piece(Assassin())
        return self.game
    
    def place_lands(self) -> Game:
        player0, player1 = self.game.players
        player0.place_land(Coordinate(0, 0))
        player1.place_land(Coordinate(0, 1))
        player0.place_land(Coordinate(0, 2))
        player1.place_land(Coordinate(0, 3))
        player0.place_land(Coordinate(1, 0))
        player1.place_land(Coordinate(2, 0))
        player0.place_land(Coordinate(2, 1))
        player1.place_land(Coordinate(2, 2))
        player0.place_land(Coordinate(1, 2))
        player1.place_land(Coordinate(1, 4))
        return self.game
    
    def place_citadels(self) -> Game:
        player0, player1 = self.game.players
        player0.place_citadel(Coordinate(2, 0))
        player1.place_citadel(Coordinate(0, 3))
        return self.game


def test_create_game():
    game = Game()


def test_choose_personal_piece(game:Game|None=None) -> Game:
    game = game or Game()

    player0 = game.players[0]
    player1 = game.players[1]

    player0.choose_personal_piece(Knight())
    player1.choose_personal_piece(Bird())
    assert not player0.is_done_choosing_personal_pieces
    assert not player1.is_done_choosing_personal_pieces
    player0.choose_personal_piece(Turtle())
    player1.choose_personal_piece(Rabbit())
    player0.choose_personal_piece(Knight())
    player1.choose_personal_piece(Bird())

    assert player0.is_done_choosing_personal_pieces
    assert player1.is_done_choosing_personal_pieces

    try:
        player0.choose_personal_piece(Knight)
    except ValueError as e:
        assert str(e) == "Players are not allowed to choose more than 3 pieces for their personal stash. 'Player 0' has already chosen 3 personal pieces."

    assert len(player0.personal_stash) == 3
    assert isinstance(player0.personal_stash[0], Knight)
    assert isinstance(player0.personal_stash[1], Turtle)
    assert isinstance(player0.personal_stash[2], Knight)
    assert len(player1.personal_stash) == 3
    assert isinstance(player1.personal_stash[0], Bird)
    assert isinstance(player1.personal_stash[1], Rabbit)
    assert isinstance(player1.personal_stash[2], Bird)

    return game


def test_choose_community_pieces(game:Game|None=None) -> Game:
    game = game or Game()

    player0 = game.players[0]
    player1 = game.players[1]

    player0builder = Builder()
    player0bomber = Bomber()
    player0necromancer = Necromancer()

    player0.choose_community_piece(player0builder)
    player0.choose_community_piece(player0bomber)
    assert not player0.is_done_choosing_community_pieces
    player0.choose_community_piece(player0necromancer)
    assert player0.is_done_choosing_community_pieces

    player1assassin = Assassin()
    player1builder = Builder()
    player1assassin2 = Assassin()

    player1.choose_community_piece(player1assassin)
    player1.choose_community_piece(player1builder)
    assert not player1.is_done_choosing_community_pieces
    player1.choose_community_piece(player1assassin2)
    assert player1.is_done_choosing_community_pieces

    try:
        player0.choose_community_piece(Builder)
    except ValueError as e:
        assert str(e) == "Players are not allowed to choose more than 3 pieces for the community pool. 'Player 0' has already chosen 3 community pieces."
    else:
        assert False, "Player 0 was allowed to choose more than 3 community pieces; should have thrown an error."

    assert game.community_pool == [player0builder, player0bomber, player0necromancer, player1assassin, player1builder, player1assassin2]
    assert player0.community_entities == [player0builder, player0bomber, player0necromancer]
    assert player1.community_entities == [player1assassin, player1builder, player1assassin2]
    

def test_place_land(game:Game|None=None):
    '''Places lands on the board and checks if the placement is valid.

    The board created by this looks like an L or a b.
    '''
    game = game or Game(lands_per_player=3)

    player0, player1 = game.players

    assert game.current_player == player0
    player0.place_land(Coordinate(0, 0))

    assert game.current_player == player1
    player1.place_land(Coordinate(0, 1))

    assert game.current_player == player0
    try:
        player0.place_land(Coordinate(0, 0))
    except PlacementError as e:
        assert "Cannot place land at" in str(e)
    else:
        assert False, "Player 0 was allowed to place land at (0, 0), which already has a land; should have thrown an error."
    
    try:
        player0.place_land(Coordinate(0, 4))
    except PlacementError as e:
        assert "Cannot place land at" in str(e)
    else:
        assert False, "Player 0 was allowed to place land at (0, 4), which is not adjacent to an existing land; should have thrown an error."
    
    player0.place_land(Coordinate(1, 0))
    player1.place_land(Coordinate(1, 1))

    assert not player0.is_done_placing_lands
    assert not player1.is_done_placing_lands
    player0.place_land(Coordinate(0, 2))
    player1.place_land(Coordinate(0, 3))
    assert player0.is_done_placing_lands
    assert player1.is_done_placing_lands

    try:
        player0.place_land(Coordinate(1, 0))
    except PlacementError as e:
        assert "Players are not allowed to place more than" in str(e)
    else:
        assert False, "Player 0 was allowed to place more than 3 lands; should have thrown an error."
    
    assert len(game.board.find_tiles(Land)) == 6
    assert game.board[Coordinate(0, 0)].has_type(Land)
    assert game.board[Coordinate(2, 2)].is_water


def test_place_citadels(game:Game|None=None):
    if game is None:
        game = Game(lands_per_player=3)
        test_place_land(game)

    player0, player1 = game.players

    player0.place_citadel(Coordinate(1, 0))
    assert player0.is_done_placing_citadels
    player1.place_citadel(Coordinate(0, 3))
    assert player1.is_done_placing_citadels


def test_place_pieces():
    example = ExampleGame()
    game = example.game
    example.choose_personal_pieces()
    example.choose_community_pieces()
    example.place_lands()
    example.place_citadels()
    player0, player1 = game.players

    player0knight = player0.personal_stash.where(Knight)[0]

    try:
        player0.place_piece(player0knight, Coordinate(2, 0))
    except PlacementError as e:
        assert "occupied" in str(e)
    else:
        assert False, "Player 0 was allowed to place a piece on their own citadel; should have thrown an error."

    try:
        player0.place_piece(player0knight, Coordinate(1, 1))
    except PlacementError as e:
        assert "TERRAIN" in str(e)
    else:
        assert False, "Player 0 was allowed to place a piece on a water tile; should have thrown an error."
    
    try:
        player0.place_piece(player0knight, Coordinate(1, 4))
    except PlacementError as e:
        assert "adjacent" in str(e)
    else:
        assert False, "Player 0 was allowed to place a piece on a tile that is not adjacent to their own citadel; should have thrown an error."
    
    player0.place_piece(player0knight, Coordinate(1, 0))

    assert player0knight in game.board[Coordinate(1, 0)]
    assert player0knight.location.coordinate == Coordinate(1, 0)