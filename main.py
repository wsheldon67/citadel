import pygame
from pygame.event import Event
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from citadel.game import Game
    from .screens.shared import Component

class App():
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
            self.current_screen.resize(event)


app = App()

if __name__ == "__main__":
    import sys
    from screens.shared import S

    S.app = app
    startup = sys.argv[1] if len(sys.argv) > 1 else 'config'

    if startup == 'config':
        from screens.config import ConfigScreen
        app.current_screen = ConfigScreen(app)

    elif startup == 'land_placement':
        from citadel.game import Game
        from screens.land_placement import LandPlacement
        app.game = Game()
        app.current_screen = LandPlacement(app)
    
    elif startup == 'piece_selection':
        from screens.piece_selection import PieceSelection, place_lands
        place_lands(app)
        app.current_screen = PieceSelection(app)

    app.run()