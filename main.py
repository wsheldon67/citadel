from citadel import *
import pygame
from pygame.event import Event
from typing import overload


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


class Button(Component):
    '''Class for a button'''
    def __init__(self, x:int, y:int, w:int, h:int, label:str, color=(200, 200, 200), font_size:int=6):
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
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.color = color
        self.font_size = font_size
        self.font = pygame.font.Font(None, int(app.to_actual(font_size)))
        app.add_listener(pygame.VIDEORESIZE, self.resize, self)
        self._x, self._y, self._w, self._h = app.to_actual(x, y, w, h)


    def render(self):
        '''Render the button'''
        surface = pygame.display.get_surface()
        rect = pygame.Rect(self._x, self._y, self._w, self._h)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, (100, 100, 100), rect, 2)
        text_surf = self.font.render(self.label, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)


    def clicked(self, pos:tuple[int, int], button:int) -> bool:
        '''Handle mouse button down events'''
        if button == pygame.BUTTON_LEFT:
            pos = app.to_relative(*pos)
            if self.x <= pos[0] <= self.x + self.w and self.y <= pos[1] <= self.y + self.h:
                print(f"Button {self.label} clicked at {pos}")
                return True
        return False
    

    def resize(self, event:Event):
        '''Handle resize events'''
        self._x, self._y, self._w, self._h = app.to_actual(self.x, self.y, self.w, self.h)
        self.font = pygame.font.Font(None, int(app.to_actual(self.font_size)))


class NumberPicker(Component):
    '''Class for a number picker'''
    def __init__(self, x:int, y:int, w:int, h:int, label:str,
            initial_value:int=0, min_value:int=0, max_value:int=50,
            font_size:int=9):
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
        self.rect = pygame.Rect(*app.to_actual(x, y, w, h))
        self.font = pygame.font.Font(None, int(app.to_actual(font_size)))
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
        self.rect = pygame.Rect(*app.to_actual(self.x, self.y, self.w, self.h))
        self.font = pygame.font.Font(None, int(app.to_actual(self.font_size)))



class ConfigScreen(Component):
    '''Class for the configuration screen'''
    def __init__(self):

        self.children = {}
        self.pickers = {
            "Number of Players": [2, 2, 12],
            "Lands per Player": [10, 2, 96],
            "Personal Pieces per Player": [3, 3, 48],
            "Community Pieces per Player": [3, 3, 48],
        }
        width = 96
        for i, (picker_name, (initial_value, min_value, max_value)) in enumerate(self.pickers.items()):
            self.children[picker_name] = NumberPicker(
                app.center[0] - (width // 2), 12 + i * 24, width, 12, picker_name, initial_value, min_value, max_value
            )
        app.add_listener(pygame.MOUSEBUTTONDOWN, self.on_click, self)
    

    def on_click(self, event:Event):
        '''Handle mouse button down events'''
        for name, child in self.children.items():
            if isinstance(child, NumberPicker):
                self.pickers[name][0] = child.get_value(event.pos, event.button)


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

    @property
    def center(self) -> tuple[int, int]:
        '''Get the center of the screen'''
        return self.to_relative(self.w // 2, self.h // 2)


    @overload
    def to_actual(self, x:int) -> float:
        '''Change a number to actual pixels'''
    @overload
    def to_actual(self, x:int, y:int, w:int, h:int) -> tuple[float, float, float, float]:
        '''Change a rectangle to actual xy pixels'''
    @overload
    def to_actual(self, x:int, y:int) -> tuple[float, float]:
        '''Change a point to actual xy pixels'''
    def to_actual(self, x, y=None, w=None, h=None):
        '''Get a rectangle '''
        if w is not None and h is not None:
            return (self.w * (x / 144), self.h * (y / 144), self.w * (w / 144), self.h * (h / 144))
        if y is not None:
            return (self.w * (x / 144), self.h * (y / 144))
        return min(self.w * (x / 144), self.h * (x / 144))


    @overload
    def to_relative(self, x:int) -> float:
        '''Change a number to relative pixels'''
    @overload
    def to_relative(self, x:int, y:int) -> tuple[float, float]:
        '''Change a rectangle to relative xy pixels'''
    @overload
    def to_relative(self, x:int, y:int, w:int, h:int) -> tuple[float, float, float, float]:
        '''Change a rectangle to relative xy pixels'''
    def to_relative(self, x, y=None, w=None, h=None):
        '''Get a rectangle '''
        if w is not None and h is not None:
            return (x * 144 / self.w, y * 144 / self.h, w * 144 / self.w, h * 144 / self.h)
        if y is not None:
            return (x * 144 / self.w, y * 144 / self.h)
        return x * 144 / min(self.w, self.h)


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