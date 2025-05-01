from will_citadel import *


class ExampleGame():

    def __init__(self):
        self.game = Game()
    
    def choose_personal_pieces(self) -> Game:
        player0, player1 = self.game.players
        player0.choose_personal_piece(Knight)
        player1.choose_personal_piece(Bird)
        player0.choose_personal_piece(Turtle)
        player1.choose_personal_piece(Rabbit)
        player0.choose_personal_piece(Knight)
        player1.choose_personal_piece(Bird)
        return self.game
    
    def choose_community_pieces(self) -> Game:
        player0, player1 = self.game.players
        player0.choose_community_piece(Builder)
        player1.choose_community_piece(Assassin)
        player0.choose_community_piece(Bomber)
        player1.choose_community_piece(Builder)
        player0.choose_community_piece(Necromancer)
        player1.choose_community_piece(Assassin)
        return self.game
    
    def place_lands(self) -> Game:
        player0, player1 = self.game.players
        player0.place(Land, Coordinate(0, 0))
        player1.place(Land, Coordinate(0, 1))
        player0.place(Land, Coordinate(0, 2))
        player1.place(Land, Coordinate(0, 3))
        player0.place(Land, Coordinate(1, 0))
        player1.place(Land, Coordinate(2, 0))
        player0.place(Land, Coordinate(2, 1))
        player1.place(Land, Coordinate(2, 2))
        player0.place(Land, Coordinate(1, 2))
        player1.place(Land, Coordinate(1, 4))
        return self.game
    
    def place_citadels(self) -> Game:
        player0, player1 = self.game.players
        player0.place(player0.personal_stash.where(Citadel)[0], self.game.board[Coordinate(2, 0)])
        player1.place(player1.personal_stash.where(Citadel)[0], self.game.board[Coordinate(0, 3)])
        return self.game
    
    def place_pieces(self) -> Game:
        player0, player1 = self.game.players
        player0.place(player0.personal_stash.where(Knight)[0], self.game.board[Coordinate(1, 0)])
        player1.place(player1.personal_stash.where(Bird)[0], self.game.board[Coordinate(0, 2)])
        return self.game
    
    def setup_full_game(self) -> Game:
        self.choose_personal_pieces()
        self.choose_community_pieces()
        self.place_lands()
        self.place_citadels()
        self.place_pieces()
        return self.game


def test_create_game():
    game = Game()


def test_choose_personal_piece(game:Game|None=None) -> Game:
    game = game or Game()

    player0 = game.players[0]
    player1 = game.players[1]

    player0.choose_personal_piece(Knight)
    player1.choose_personal_piece(Bird)
    assert not player0.is_done_choosing_personal_pieces
    assert not player1.is_done_choosing_personal_pieces
    player0.choose_personal_piece(Turtle)
    player1.choose_personal_piece(Rabbit)
    player0.choose_personal_piece(Knight)
    player1.choose_personal_piece(Bird)

    assert player0.is_done_choosing_personal_pieces
    assert player1.is_done_choosing_personal_pieces

    try:
        player0.choose_personal_piece(Knight)
    except ValueError as e:
        assert str(e) == "Players are not allowed to choose more than 3 pieces for their personal stash. 'Player 0' has already chosen 3 personal pieces."

    assert len(player0.personal_stash.where(Piece)) == 3
    assert len(player0.personal_stash.where(Knight)) == 2
    assert len(player0.personal_stash.where(Turtle)) == 1
    assert len(player1.personal_stash.where(Piece)) == 3
    assert len(player1.personal_stash.where(Bird)) == 2
    assert len(player1.personal_stash.where(Rabbit)) == 1

    return game


def test_choose_community_pieces(game:Game|None=None) -> Game:
    game = game or Game()

    player0 = game.players[0]
    player1 = game.players[1]

    choose_from = EntityList(game)

    player0builder = Builder(choose_from, player0)
    player0bomber = Bomber(choose_from, player0)
    player0necromancer = Necromancer(choose_from, player0)

    player0.choose_community_piece(player0builder)
    player0.choose_community_piece(player0bomber)
    assert not player0.is_done_choosing_community_pieces
    player0.choose_community_piece(player0necromancer)
    assert player0.is_done_choosing_community_pieces

    player1assassin = Assassin(choose_from, player1)
    player1builder = Builder(choose_from, player1)
    player1assassin2 = Assassin(choose_from, player1)

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

    player0.place(Land, Coordinate(0, 0))
    assert game.board[Coordinate(0, 0)].where(Land), "Player 0's land was not placed correctly."
    assert len(player0.personal_stash.where(Land)) == 2, "Player 0's land was not removed from their personal stash."
    player1.place(Land, Coordinate(0, 1))

    try:
        player0.place(Land, Coordinate(0, 0))
    except ActionError as e:
        assert "cannot add Land" in str(e)
    else:
        assert False, "Player 0 was allowed to place land at (0, 0), which already has a land; should have thrown an error."
    
    try:
        player0.place(Land, Coordinate(0, 4))
    except ActionError as e:
        assert "adjacent" in str(e)
    else:
        assert False, "Player 0 was allowed to place land at (0, 4), which is not adjacent to an existing land; should have thrown an error."
    
    player0.place(Land, Coordinate(1, 0))
    player1.place(Land, Coordinate(1, 1))

    assert not player0.is_done_placing_lands
    assert not player1.is_done_placing_lands
    player0.place(Land, Coordinate(0, 2))
    player1.place(Land, Coordinate(0, 3))
    assert player0.is_done_placing_lands
    assert player1.is_done_placing_lands

    try:
        player0.place(Land, Coordinate(1, 2))
    except ActionError as e:
        assert "not found" in str(e)
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

    player0.perform_action(Citadel, 'place', Coordinate(1, 0))
    assert player0.is_done_placing_citadels
    player1.perform_action(Citadel, 'place', Coordinate(0, 3))
    assert player1.is_done_placing_citadels


def test_place_pieces():
    example = ExampleGame()
    game = example.game
    example.choose_personal_pieces()
    example.choose_community_pieces()
    example.place_lands()
    example.place_citadels()
    player0, player1 = game.players

    player0knight:Knight = player0.personal_stash.where(Knight)[0]

    try:
        player0.perform_action(player0knight, 'place', Coordinate(2, 0))
    except ActionError as e:
        assert "occupied" in str(e)
    else:
        assert False, "Player 0 was allowed to place a piece on their own citadel; should have thrown an error."

    try:
        player0.perform_action(player0knight, 'place', Coordinate(1, 1))
    except ActionError as e:
        assert "TERRAIN" in str(e)
    else:
        assert False, "Player 0 was allowed to place a piece on a water tile; should have thrown an error."
    
    try:
        player0.perform_action(player0knight, 'place', Coordinate(1, 4))
    except ActionError as e:
        assert "adjacent" in str(e)
    else:
        assert False, "Player 0 was allowed to place a piece on a tile that is not adjacent to their own citadel; should have thrown an error."
    
    player0.perform_action(player0knight, 'place', Coordinate(1, 0))

    assert player0knight in game.board[Coordinate(1, 0)]
    assert player0knight.location.coordinate == Coordinate(1, 0)


def test_move_pieces():
    game = ExampleGame().setup_full_game()
    player0, player1 = game.players

    player0knight:Knight = game.board.where(Knight, owner=player0)[0]
    player1bird:Bird = game.board.where(Bird, owner=player1)[0]

    try:
        player0.move(player0knight, Coordinate(1, -1))
    except ActionError as e:
        assert "TERRAIN" in str(e)
    else:
        assert False, "Player 0 was allowed to move a piece to a water tile; should have thrown an error."
    
    player0knight.move(game.board[Coordinate(0, 0)], player0)
    assert player0knight in game.board[Coordinate(0, 0)], "Player 0's knight was not moved to the correct tile."
    assert player0knight.location.coordinate == Coordinate(0, 0), "Player 0's knight's location was not updated correctly."
    assert player0knight not in game.board[Coordinate(1, 0)], "Player 0's knight was not removed from the previous tile."


def test_capture_pieces():
    game = ExampleGame().setup_full_game()
    player0, player1 = game.players

    player0knight:Knight = game.board.where(Knight, owner=player0)[0]
    player1bird:Bird = game.board.where(Bird, owner=player1)[0]

    player0.move(player0knight, game.board[Coordinate(0, 0)])

    player1.capture(player1bird, Coordinate(0, 0))
    target_tile = game.board[Coordinate(0, 0)]
    capture_action = player1bird.actions(target_tile, player1)['capture']
    capture_action.execute(target_tile, player1)

    assert player1bird in game.board[Coordinate(0, 0)]
    assert player1bird.location.coordinate == Coordinate(0, 0)
    assert player1bird.owner == player1
    assert player0knight not in game.board[Coordinate(0, 0)]
    assert player0knight.location == game.graveyard


def test_entity_list_where():
    game = Game()
    el = EntityList(game)
    added_knight = Knight(el)
    el.append(added_knight)
    assert added_knight.location == el, "The knight's location was not set to the EntityList when added."

    found_knight = el.where(Knight)[0]
    assert added_knight == found_knight, "The knight added to the EntityList was not found by the where method."
    assert added_knight.location == found_knight.location, "The knight's location was not preserved when added to the EntityList."
    assert found_knight.location == el, "The knight's location was not set to the EntityList when added."


def test_entity_list_json():
    game = Game()
    el = EntityList(game, name='original')
    added_knight = Knight(el)
    el.append(added_knight)

    json_data = el.to_json()
    assert json_data == {
        'name': 'original',
        'entities': [added_knight.to_json()]
    }, "The JSON representation of the EntityList is not correct."

    new_el = EntityList.from_json(json_data, game)
    assert new_el.name == el.name, "The name of the new EntityList is not correct."
    assert len(new_el) == len(el), "The number of entities in the new EntityList is not correct."
    assert new_el[0].to_json() == el[0].to_json(), "The entity in the new EntityList is not the same as the original."
    assert new_el[0].location == new_el, "The entity's location in the new EntityList is not correct."


def test_board_json():
    game = Game()
    board = game.board
    land = game.players[0].personal_stash.where(Land)[0]
    game.players[0].place(land, Coordinate(0, 0))
    board_json = board.to_json()

    assert board_json == {
        'name': 'main',
        'tiles': {
            '0,0': board[Coordinate(0, 0)].to_json(),
        },
    }, "The JSON representation of the board is not correct."

    new_board = Board.from_json(board_json, game)
    assert new_board.name == board.name, "The name of the new board is not correct."
    assert len(new_board) == len(board), "The number of tiles in the new board is not correct."
    assert new_board[Coordinate(0, 0)].to_json() == board[Coordinate(0, 0)].to_json(), "The tile in the new board is not the same as the original."


def test_game_json():
    game = ExampleGame().setup_full_game()
    game_json = game.to_json()

    new_game = Game.from_json(game_json)

    assert new_game.players[0].name == game.players[0].name, "The name of the first player in the new game is not correct."
    assert new_game.board.name == game.board.name, "The name of the board in the new game is not correct."
    assert len(new_game.players[0].personal_stash) == len(game.players[0].personal_stash), "The number of entities in the first player's personal stash in the new game is not correct."
    assert len(new_game.players[0].community_entities) == len(game.players[0].community_entities), "The number of entities in the first player's community entities in the new game is not correct."
    assert len(new_game.community_pool) == len(game.community_pool), "The number of entities in the community pool in the new game is not correct."
    assert new_game.board[Coordinate(0, 0)].to_json() == game.board[Coordinate(0, 0)].to_json(), "The tile in the new board is not the same as the original."
    assert new_game.board.where(Knight)[0].to_json() == game.board.where(Knight)[0].to_json(), "The knight in the new board is not the same as the original."


