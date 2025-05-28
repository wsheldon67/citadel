from __future__ import annotations
import pygame
from pygame.event import Event
from abc import ABC
from typing import Self, TYPE_CHECKING

from citadel.util import Layer

if TYPE_CHECKING:
    from ..citadel.game import Game
    from ..citadel.entity import Entity, EntityList
    from ..citadel.board import Tile, Board



class Component(ABC):
    '''Base class for all components'''
    def __init__(self):
        self.children:dict[str, Component] = {}
        self.z_index = 0  # Default z-index
        

    def get_children_sorted_by_z(self):
        """Return children sorted by z-index (highest first)"""
        return sorted(self.children.values(), key=lambda c: c.z_index if hasattr(c, 'z_index') else 0, reverse=True)


    def render(self):
        '''Render the component'''
        for child in self.children.values():
            child.render()
    

    def handle_event(self, event:Event):
        pass


    def update(self):
        '''Readjust the component's properties based on new state.'''
        pass


    def resize(self, event:Event|None=None):
        '''Update the component's size and position based on a window resize.'''
        pass



class S(float):
    '''Base class for scaling'''
    def __new__(cls, value:float):
        '''Create a new instance of S'''
        return super().__new__(cls, value)
    
    @property
    def p(self) -> float:
        '''Get the value as actual screen pixels.'''
        from main import get_app
        app = get_app()
        return min(app.w, app.h) * self / 144

    def __add__(self, other:float|Self) -> Self:
        '''Add two S values'''
        return self.__class__(super().__add__(other))
    
    def __sub__(self, other:float|Self) -> Self:
        '''Subtract two S values'''
        return self.__class__(super().__sub__(other))
    
    def __mul__(self, other:float|Self) -> Self:
        '''Multiply two S values'''
        return self.__class__(super().__mul__(other))

    def __truediv__(self, other:float|Self) -> Self:
        '''Divide two S values'''
        return self.__class__(super().__truediv__(other))

    def __floordiv__(self, other:float|Self) -> Self:
        '''Floor divide two S values'''
        return self.__class__(super().__floordiv__(other))

    def __mod__(self, other:float|Self) -> Self:
        '''Modulo two S values'''
        return self.__class__(super().__mod__(other))


class X(S):
    @property
    def p(self) -> float:
        '''Get the value as actual screen pixels.'''
        from main import get_app
        app = get_app()
        return app.w * self / 144

class Y(S):
    @property
    def p(self) -> float:
        '''Get the value as actual screen pixels.'''
        from main import get_app
        app = get_app()
        return app.h * self / 144
    


class Clickable(Component):
    '''Base class for clickable components'''
    def __init__(self, x:S, y:S, w:S, h:S):
        super().__init__()
        self.rect = pygame.Rect(x.p, y.p, w.p, h.p)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.clickable = True
    

    def resize(self, event:Event|None=None):
        '''Handle resize events'''
        self.rect = pygame.Rect(self.x.p, self.y.p, self.w.p, self.h.p)



class Button(Clickable):
    '''Class for a button'''
    def __init__(self, x:S, y:S, w:S, h:S, label:str, color=(200, 200, 200), font_size:S=S(6)):
        '''Initialize the button
        Args:
            x: X position of top left corner
            y: Y position of top left corner
            w: Width of the button
            h: Height of the button
            label: A text label to identify the button
            color: Color of the button
            font_size: Font size of the button label
        '''
        super().__init__(x, y, w, h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.color = color
        self.font_size = font_size
        self.resize()


    def render(self):
        '''Render the button'''
        surface = pygame.display.get_surface()
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)
        text_surf = self.font.render(self.label, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    

    def resize(self, event:Event|None=None):
        '''Handle resize events'''
        super().resize(event)
        self.font = pygame.font.Font(None, int(self.font_size.p))


class NumberPicker(Component):
    '''Class for a number picker'''
    def __init__(self, x:S, y:S, w:S, h:S, label:str,
            initial_value:int=0, min_value:int=0, max_value:int=50,
            font_size:S=S(9)):
        '''Initialize the number picker
        Args:
            x: X position of top left corner
            y: Y position of top left corner
            width: Width of the whole component
            height: Height of the whole component
            label: A text label to identify the picker
            initial_value: Initial value
            min_value: Minimum value
            max_value: Maximum value
            font_size: Font size of the label
        '''
        self.x = x
        self.y = y
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.w = w
        self.h = h
        self.font_size = font_size
        self.rect = pygame.Rect(x.p, y.p, w.p, h.p)
        self.font = pygame.font.Font(None, int(font_size.p))
        self.children = {
            "button_up": Button(x + w - h, y, h, h, "+", font_size=font_size),
            "button_down": Button(x, y, h, h, "-", font_size=font_size),
        }


    def render(self):
        '''Render the number picker'''
        surface = pygame.display.get_surface()
        text_surf = self.font.render(f"{self.label}: {self.value}", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        surface.blit(text_surf, text_rect)
        super().render()


    def get_value(self, event:Event) -> int:
        '''Handle mouse button down events'''
        from main import get_app
        app = get_app()
        clicked:Button = app.get_component_at_position(event.pos, self)
        if clicked.label == "+":
            if self.value < self.max_value:
                self.value += 1
        elif clicked.label == "-":
            if self.value > self.min_value:
                self.value -= 1
        return self.value
    

    def resize(self, event:Event):
        '''Handle resize events'''
        self.rect = pygame.Rect(self.x.p, self.y.p, self.w.p, self.h.p)
        self.font = pygame.font.Font(None, int(self.font_size.p))


def colorize_black_and_transparent(surface:pygame.Surface, new_color:tuple) -> pygame.Surface:  
    """
    Change black lines to a new color while preserving transparency.
    Perfect for images that only have black and transparent pixels.
    
    Args:
        surface: The pygame Surface with black lines
        new_color: RGB tuple of the desired color (e.g. (255, 0, 0) for red)
                   Can include alpha as fourth value if needed
    
    Returns:
        A new Surface with colored lines
    """
    width, height = surface.get_size()
    colored = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Extend the color with alpha if needed
    if len(new_color) == 3:
        full_color = (*new_color, 255)
    else:
        full_color = new_color
        
    # For each pixel, keep the transparency but change the color
    for x in range(width):
        for y in range(height):
            pixel = surface.get_at((x, y))
            if pixel[3] > 0:  # If not fully transparent
                colored.set_at((x, y), (full_color[0], full_color[1], full_color[2], pixel[3]))
    
    return colored


class DrawEntity(Clickable):
    def __init__(self, entity:Entity, x:S, y:S, s:S):
        super().__init__(x, y, s, s)
        self.entity = entity
        self.x, self.y, self.s = x, y, s
        self.img = pygame.image.load(f"img/{entity.img}").convert_alpha()
        if entity.color:
            self.img = colorize_black_and_transparent(self.img, self.entity.color)


    def render(self):
        '''Render the entity'''
        img = pygame.transform.scale(self.img, (self.s.p, self.s.p))
        rect = pygame.Rect(self.x.p, self.y.p, self.s.p, self.s.p)
        surface = pygame.display.get_surface()
        surface.blit(img, rect)


class DrawWater(Component):
    def __init__(self, x:S, y:S, s:S):
        super().__init__()
        self.x, self.y = x, y
        self.s = s
        self.z_index = 1
        self.img = pygame.image.load("img/water.png").convert_alpha()


    def render(self):
        '''Render the water'''
        img = pygame.transform.scale(self.img, (self.s.p, self.s.p))
        rect = pygame.Rect(self.x.p, self.y.p, self.s.p, self.s.p)
        surface = pygame.display.get_surface()
        surface.blit(img, rect)

        

class DrawTile(Clickable):
    def __init__(self, tile:Tile, x:S, y:S, s:S):
        super().__init__(x, y, s, s)
        self.tile = tile
        self.x, self.y = x, y
        self.s = s
        self.z_index = 0
        self.children['water'] = DrawWater(x, y, s)
        self.children['water'].clickable = False
        if tile.get_by_layer(Layer.TERRAIN):
            self.children['terrain'] = DrawEntity(tile.get_by_layer(Layer.TERRAIN), x, y, s)
            self.children['terrain'].z_index = 2
            self.children['terrain'].clickable = False
        if tile.get_by_layer(Layer.PIECE):
            shrunk = s * 0.9
            diff = s - shrunk
            self.children['piece'] = DrawEntity(tile.get_by_layer(Layer.PIECE),
                x + diff/2, y + diff/2, shrunk)
            self.children['piece'].z_index = 3
            self.children['piece'].clickable = False



class DrawBoard(Component):
    def __init__(self, board:Board, x:S, y:S, w:S, h:S):
        super().__init__()
        self.board = board
        self.board.on_update = self.update
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.s = S(12)
        self.z_index = 0
        self.update()
        

    def update(self):
        '''Set the children of the board'''
        for ix, iy in self.board.extents.add_margin(2):
            tile_x = S(float(self.x) + ix * self.s)
            tile_y = S(float(self.y) + iy * self.s)
            self.children[f"{ix},{iy}"] = DrawTile(
                self.board[(ix, iy)],
                tile_x,
                tile_y,
                self.s
                )


class DrawEntityList(Component):
    def __init__(self, entities:EntityList, x:S, y:S, w:S, h:S):
        super().__init__()
        self.entities = entities
        self.entities.on_update = self.update
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.s = S(12)
        self.z_index = 1
        self.update()
    

    def render(self):
        rect = pygame.Rect(self.x.p, self.y.p, self.w.p, self.h.p)
        surface = pygame.display.get_surface()
        pygame.draw.rect(surface, (60, 60, 60), rect)
        super().render()
    

    def update(self):
        '''Set the children of the entity list'''
        self.children.clear()
        for i, entity in enumerate(self.entities):
            entity_x = X(self.x + (i % 2) * self.s)
            entity_y = Y(self.y + (i // 2) * self.s)
            self.children[f"{entity}{i}"] = DrawEntity(
                entity,
                entity_x,
                entity_y,
                self.s
                )