from will_citadel import Game, Coordinate
from will_citadel import Bird, Knight, Turtle, Rabbit, Builder, Bomber, Necromancer, Assassin
from will_citadel import Land

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
    assert player0.community_pieces == [player0builder, player0bomber, player0necromancer]
    assert player1.community_pieces == [player1assassin, player1builder, player1assassin2]
    

def test_place_land(game:Game|None=None):
    game = game or Game(lands_per_player=3)

    player0, player1 = game.players

    assert game.current_player == player0
    player0.place_land(Coordinate(0, 0))

    assert game.current_player == player1
    player1.place_land(Coordinate(0, 1))

    assert game.current_player == player0
    try:
        player0.place_land(Coordinate(0, 0))
    except ValueError as e:
        assert "Cannot place land at" in str(e)
    else:
        assert False, "Player 0 was allowed to place land at (0, 0), which already has a land; should have thrown an error."
    
    try:
        player0.place_land(Coordinate(0, 4))
    except ValueError as e:
        assert "Cannot place land at" in str(e)
    else:
        assert False, "Player 0 was allowed to place land at (0, 4), which is not adjacent to an existing land; should have thrown an error."
    
    assert not player0.is_done_placing_lands
    assert not player1.is_done_placing_lands
    player0.place_land(Coordinate(0, 2))
    player1.place_land(Coordinate(0, 3))
    assert player0.is_done_placing_lands
    assert player1.is_done_placing_lands

    try:
        player0.place_land(Coordinate(1, 0))
    except ValueError as e:
        assert "Players are not allowed to place more than" in str(e)
    else:
        assert False, "Player 0 was allowed to place more than 3 lands; should have thrown an error."
    
    assert len(game.board.find_tiles_by_entity_type(Land)) == 6