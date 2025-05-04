

Board
=======

The Board is a collection of :doc:`tile` s, indexed by :doc:`coordinate`.

You can reference *any* tile on the infinite board by its coordinates:

    tile = game.board[Coordinate(0, 0)]  # The tile at (0, 0)

Any coordinate that has nothing on it will return an empty :doc:`tile`.