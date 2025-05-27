from citadel import *
import pygame
from pygame.event import Event
from typing import overload, Self
from abc import ABC
import warnings


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



class ConfigScreen(Component):
    '''Class for the configuration screen'''
    def __init__(self):

        self.children = {
            "Continue": Button(X(72), Y(120), X(36), Y(12), "Continue"),
        }
        self.pickers = {
            "Number of Players": [2, 2, 2],
            "Lands per Player": [5, 2, 18],
            "Personal Pieces per Player": [2, 1, 18],
            "Community Pieces per Player": [2, 1, 18],
        }
        width = X(120)
        for i, (picker_name, (initial_value, min_value, max_value)) in enumerate(self.pickers.items()):
            self.children[picker_name] = NumberPicker(
                X(72) - (width // 2), Y(12 + i*24), width, Y(12),
                picker_name, initial_value, min_value, max_value
            )


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.on_click(event)
    

    def on_click(self, event:Event):
        '''Handle mouse button down events'''
        clicked = app.get_component_at_position(event.pos, self)
        if clicked is None:
            return
        for name, child in self.children.items():
            if isinstance(child, NumberPicker) and clicked in child.children.values():
                self.pickers[name][0] = child.get_value(event)
        
        if clicked == self.children["Continue"]:
            print("Continue clicked")
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
        self.resize()
    

    def handle_event(self, event):
        '''Handle events for the land placement screen'''
        if event.type == pygame.MOUSEMOTION:
            self.on_mouse_motion(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.on_click(event)


    def on_mouse_motion(self, event:Event):
        if app.selected and isinstance(app.selected, DrawEntity):
            pos = event.pos
            app.selected.x = X(float(pos[0] / app.w * 144) - app.selected.s / 2)
            app.selected.y = Y(float(pos[1] / app.h * 144) - app.selected.s / 2)
    

    def on_click(self, event:Event):
        clicked = app.get_component_at_position(event.pos)
        if app.selected and clicked is None:
            self.deselect()
        elif app.selected and isinstance(clicked, DrawTile):
            self.place(clicked)
        elif not app.selected and isinstance(clicked, DrawEntity):
            app.selected = clicked
            app.selected.clickable = False


    def place(self, on_tile:DrawTile):
        actions = app.selected.entity.actions(on_tile.tile, app.game.current_player)
        if 'place' in actions:
            try:
                app.game.current_player.place(app.selected.entity, on_tile.tile)
                print(f"Placed {app.selected.entity} on {on_tile.tile}")
                print(f"Current player: {app.game.current_player}")
                app.selected = None
            except ActionError as e:
                print(e)
                self.deselect()
    

    def deselect(self):
        '''Deselect the currently selected entity'''
        app.selected.clickable = True
        app.selected = None
        for child in self.children.values():
            child.update()

    
    def render(self):
        super().render()
        if app.selected and isinstance(app.selected, DrawEntity):
            app.selected.render()


class App:
    def __init__(self):
        pygame.init()
        self.w = 960
        self.h = 640
        self.screen = pygame.display.set_mode((self.w, self.h), flags=pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen:Component = None
        self.game:Game = None
        self.selected:Component|None = None


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
    

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.quit(event)
        elif event.type == pygame.VIDEORESIZE:
            self.resize(event)
            self.current_screen.handle_event(event)
        else:
            self.current_screen.handle_event(event)



    def get_component_at_position(self, pos, component=None):
        """Find the deepest clickable component that contains the position"""
        if component is None:
            component = self.current_screen
                
        # Check if this component contains the position
        if (not hasattr(component, 'rect')) or component.rect.collidepoint(pos):
            # Check children first (depth-first)
            for child in component.get_children_sorted_by_z():
                hit_component = self.get_component_at_position(pos, child)
                if hit_component:
                    return hit_component
                    
            # If no children contain the point, check if this component is clickable
            is_clickable = component.clickable if hasattr(component, 'clickable') else True
            

            # Return this component if it's clickable
            if is_clickable and hasattr(component, 'rect'):
                return component
            # If not clickable, return None so parent components can be checked
        return None
    

    def quit(self, event:Event):
        '''Quit the application'''
        self.running = False
        print("Quitting...")
    

    def resize(self, event:Event):
        '''Match app variable to screen size'''
        self.w, self.h = event.w, event.h
        if self.current_screen:
            for child in self.current_screen.children.values():
                if hasattr(child, 'resize'):
                    child.resize(event)
        

app = App()


if __name__ == "__main__":
    app.current_screen = ConfigScreen()
    app.run()