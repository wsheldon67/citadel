from typing import Literal
from enum import Enum
from typing import NamedTuple, Iterator, Self

class BoolWithReason():
    '''A string that can be used as a boolean with a reason.
    '''
    def __init__(self, value:Literal[True]|str):
        '''Create a new BoolWithReason.

        Args:
            value: True, or a string that describes the reason for failure.
        '''
        if isinstance(value, str):
            self.reason = value
            self.value = False
        else:
            self.reason = None
            self.value = True
        
    def __bool__(self) -> bool:
        return self.value
    
    def __repr__(self) -> str:
        return f"BoolWithReason({self.value or self.reason})"


class Layer(Enum):
    '''The layer of an entity.'''
    TERRAIN = 0
    PIECE = 1


class ActionError(Exception):
    pass

class PlacementError(ActionError):
    pass


class GamePhase(Enum):
    '''The phase of the game.'''
    LAND_PLACEMENT = 0
    CITADEL_PLACEMENT = 1
    PIECE_SELECTION = 2
    BATTLE = 3
    END = 4


class Coordinate(NamedTuple):
    '''A coordinate on the board.'''
    x: int
    y: int


    def to_json(self) -> str:
        return f"{self.x},{self.y}"
    

    @classmethod
    def from_json(cls, json_data:str) -> 'Coordinate':
        x, y = json_data.split(',')
        return cls(int(x), int(y))
    

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
    
    def __sub__(self, other:'Coordinate') -> 'Coordinate':
        '''Subtract two coordinates.'''
        return Coordinate(self.x - other.x, self.y - other.y)
    
    def __add__(self, other:'Coordinate') -> 'Coordinate':
        '''Add two coordinates.'''
        return Coordinate(self.x + other.x, self.y + other.y)

    def __str__(self):
        return f"({self.x}, {self.y})"



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
    
    def add_margin(self, margin:int) -> Self:
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

    def __iter__(self) -> Iterator[Coordinate]:
        '''Iterate over the coordinates in the rectangle.'''
        for x in range(self.x_min, self.x_max + 1):
            for y in range(self.y_min, self.y_max + 1):
                yield Coordinate(x, y)