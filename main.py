from citadel import *
import pygame
from pygame.event import Event
from typing import overload, Self
from abc import ABC


class Component(ABC):
    '''Base class for all components'''
    def __init__(self):
        self.children:dict[str, Component] = {}


    def render(self):
        '''Render the component'''
        for child in self.children.values():
            child.render()


    def destroy(self):
        '''Destroy the component and all child components.'''
        app.remove_listeners(self)
        for child in self.children.values():
            child.destroy()


class S(float):
    '''Base class for scaling'''
    def __new__(cls, value:float):
        '''Create a new instance of S'''
        return super().__new__(cls, value)
    
    @property
    def p(self) -> float:
        '''Get the value as actual screen pixels.'''
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
        return app.w * self / 144

class Y(S):
    @property
    def p(self) -> float:
        '''Get the value as actual screen pixels.'''
        return app.h * self / 144


class Button(Component):
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
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.color = color
        self.font_size = font_size
        self.font = pygame.font.Font(None, int(font_size.p))


    def render(self):
        '''Render the button'''
        surface = pygame.display.get_surface()
        rect = pygame.Rect(self.x.p, self.y.p, self.w.p, self.h.p)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, (100, 100, 100), rect, 2)
        text_surf = self.font.render(self.label, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)


    def clicked(self, pos:tuple[int, int], button:int) -> bool:
        '''Handle mouse button down events'''
        if button == pygame.BUTTON_LEFT:
            if self.x.p <= pos[0] <= self.x.p + self.w.p and self.y.p <= pos[1] <= self.y.p + self.h.p:
                print(f"Button {self.label} clicked at {pos}")
                return True
        return False


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
        app.add_listener(pygame.VIDEORESIZE, self.resize, self)


    def render(self):
        '''Render the number picker'''
        surface = pygame.display.get_surface()
        text_surf = self.font.render(f"{self.label}: {self.value}", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        surface.blit(text_surf, text_rect)
        super().render()


    def get_value(self, pos:tuple[int, int], button:int) -> int:
        '''Handle mouse button down events'''
        if self.children["button_up"].clicked(pos, button):
            if self.value < self.max_value:
                self.value += 1
        elif self.children["button_down"].clicked(pos, button):
            if self.value > self.min_value:
                self.value -= 1
        return self.value
    

    def resize(self, event:Event):
        '''Handle resize events'''
        self.rect = pygame.Rect(self.x.p, self.y.p, self.w.p, self.h.p)
        self.font = pygame.font.Font(None, int(self.font_size.p))



class ConfigScreen(Component):
    '''Class for the configuration screen'''
    def __init__(self):

        self.children = {
            "Continue": Button(X(72), Y(120), X(36), Y(12), "Continue"),
        }
        self.pickers = {
            "Number of Players": [2, 2, 12],
            "Lands per Player": [10, 2, 96],
            "Personal Pieces per Player": [3, 1, 48],
            "Community Pieces per Player": [3, 1, 48],
        }
        width = X(120)
        for i, (picker_name, (initial_value, min_value, max_value)) in enumerate(self.pickers.items()):
            self.children[picker_name] = NumberPicker(
                X(72) - (width // 2), Y(12 + i*24), width, Y(12),
                picker_name, initial_value, min_value, max_value
            )
        app.add_listener(pygame.MOUSEBUTTONDOWN, self.on_click, self)
    

    def on_click(self, event:Event):
        '''Handle mouse button down events'''
        for name, child in self.children.items():
            if isinstance(child, NumberPicker):
                self.pickers[name][0] = child.get_value(event.pos, event.button)
        
        if self.children["Continue"].clicked(event.pos, event.button):
            print("Continue clicked")
            app.current_screen.destroy()
            app.game = Game(
                self.pickers["Number of Players"][0],
                self.pickers["Lands per Player"][0],
                self.pickers["Personal Pieces per Player"][0],
                self.pickers["Community Pieces per Player"][0],
                )
            app.current_screen = LandPlacement()


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


class DrawEntity(Component):
    def __init__(self, entity:Entity, x:S, y:S, s:S):
        super().__init__()
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
        self.img = pygame.image.load("img/water.png").convert_alpha()


    def render(self):
        '''Render the water'''
        img = pygame.transform.scale(self.img, (self.s.p, self.s.p))
        rect = pygame.Rect(self.x.p, self.y.p, self.s.p, self.s.p)
        surface = pygame.display.get_surface()
        surface.blit(img, rect)

        

class DrawTile(Component):
    def __init__(self, tile:Tile, x:S, y:S, s:S):
        super().__init__()
        self.tile = tile
        self.x, self.y = x, y
        self.s = s
        self.children['water'] = DrawWater(x, y, s)
        if tile.get_by_layer(Layer.TERRAIN):
            self.children['terrain'] = DrawEntity(tile.get_by_layer(Layer.TERRAIN), x, y, s)
        if tile.get_by_layer(Layer.PIECE):
            shrunk = s * 0.9
            diff = s - shrunk
            self.children['piece'] = DrawEntity(tile.get_by_layer(Layer.PIECE),
                x + diff/2, y + diff/2, shrunk)


class DrawBoard(Component):
    def __init__(self, board:Board, x:S, y:S, w:S, h:S):
        super().__init__()
        self.board = board
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.s = S(12)
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
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.s = S(12)
        self.update()
    

    def render(self):
        rect = pygame.Rect(self.x.p, self.y.p, self.w.p, self.h.p)
        surface = pygame.display.get_surface()
        pygame.draw.rect(surface, (60, 60, 60), rect)
        super().render()
    

    def update(self):
        '''Set the children of the entity list'''
        for i, entity in enumerate(self.entities):
            entity_x = X(self.x + (i % 2) * self.s)
            entity_y = Y(self.y + (i // 2) * self.s)
            self.children[f"{entity}{i}"] = DrawEntity(
                entity,
                entity_x,
                entity_y,
                self.s
                )


class LandPlacement(Component):
    '''Class for the land placement screen'''
    def __init__(self):
        super().__init__()
        self.children = {
            "board": DrawBoard(app.game.board, X(72), Y(72), X(144-36), Y(144-36)),
            "player0": DrawEntityList(app.game.players[0].personal_stash,
                X(144) - X(24), Y(0), X(24), Y(144)),
            "player1": DrawEntityList(app.game.players[1].personal_stash,
                X(0), Y(0), X(24), Y(144)),
            }


class App:
    def __init__(self):
        pygame.init()
        self.w = 960
        self.h = 640
        self.screen = pygame.display.set_mode((self.w, self.h), flags=pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen:Component = None
        self.listeners:dict[int, list[tuple[callable, Component]]] = {
            pygame.VIDEORESIZE: [(self.resize, self)],
            pygame.MOUSEBUTTONDOWN: [],
            pygame.KEYDOWN: [],
            pygame.QUIT: [(self.quit, self)],
            }
        self.game:Game = None


    def run(self):
        '''Main loop of the application'''
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            self.screen.fill((0, 0, 0))

            self.current_screen.render()

            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        print("Exiting...")
    

    def handle_event(self, event:Event):
        '''Handle events'''
        if event.type in self.listeners:
            for callback, _ in self.listeners[event.type]:
                callback(event)
    


    def add_listener(self, event_type:int, callback:Callable, component:Component):
        '''Add an event listener'''
        self.listeners[event_type].append((callback, component))
    

    def remove_listeners(self, component:Component):
        '''Remove all event listeners for a component'''
        for event_type, listeners in self.listeners.items():
            self.listeners[event_type] = [l for l in listeners if l[1] != component]
    

    def quit(self, event:Event):
        '''Quit the application'''
        self.running = False
        print("Quitting...")
    

    def resize(self, event:Event):
        '''Match app variable to screen size'''
        self.w, self.h = event.w, event.h
        

app = App()


if __name__ == "__main__":
    app.current_screen = ConfigScreen()
    app.run()