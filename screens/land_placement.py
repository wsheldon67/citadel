import pygame
from pygame.event import Event
from typing import TYPE_CHECKING

from .shared import DrawBoard, DrawEntityList, DrawEntity, DrawTile
from .shared import Component, X, Y, MessageLog, Button

from citadel.util import ActionError, GamePhase

if TYPE_CHECKING:
    from main import App


class LandPlacement(Component):
    '''The land placement screen'''
    def __init__(self, app:'App'):
        super().__init__()
        self.app = app
        self.children = {
            "board": DrawBoard(app.game.board, X(72), Y(72), X(144-36), Y(144-36)),
            "player0": DrawEntityList(app.game.players[0].personal_stash,
                X(144) - X(24), Y(0), X(24), Y(144)),
            "player1": DrawEntityList(app.game.players[1].personal_stash,
                X(0), Y(0), X(24), Y(144)),
            "message_log": MessageLog(X(0), Y(144-24), X(144), Y(24)),
            }
        self.resize()
    

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.on_mouse_motion(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.on_click(event)


    def on_mouse_motion(self, event:Event):
        if self.app.selected and isinstance(self.app.selected, DrawEntity):
            pos = event.pos
            self.app.selected.x = X(float(pos[0] / self.app.w * 144) - self.app.selected.s / 2)
            self.app.selected.y = Y(float(pos[1] / self.app.h * 144) - self.app.selected.s / 2)
    

    def on_click(self, event:Event):
        clicked = self.app.get_component_at_position(event.pos)
        if self.app.selected and clicked is None:
            self.deselect()
        elif self.app.selected and isinstance(clicked, DrawTile):
            self.place(clicked)
        elif not self.app.selected and isinstance(clicked, DrawEntity):
            self.app.selected = clicked
            self.app.selected.clickable = False
        
        done_placing_lands = all([player.is_done_placing_lands for player in self.app.game.players])
        done_placing_citadels = all([player.is_done_placing_citadels for player in self.app.game.players])
        if done_placing_lands and done_placing_citadels:
            from .piece_selection import PieceSelection
            self.app.game.phase = GamePhase.PIECE_SELECTION
            self.app.current_screen = PieceSelection(self.app)
            

    def place(self, on_tile:DrawTile):
        actions = self.app.selected.entity.actions(on_tile.tile, self.app.game.current_player)
        if 'place' in actions:
            try:
                self.app.game.current_player.place(self.app.selected.entity, on_tile.tile)
                print(f"Placed {self.app.selected.entity} on {on_tile.tile}")
                print(f"Current player: {self.app.game.current_player}")
                self.app.selected = None
            except ActionError as e:
                print(e)
                self.children['message_log'].add_message(str(e))
                self.deselect()
    

    def deselect(self):
        '''Deselect the currently selected entity'''
        self.app.selected.clickable = True
        self.app.selected = None
        for child in self.children.values():
            child.update()

    
    def render(self):
        super().render()
        if self.app.selected and isinstance(self.app.selected, DrawEntity):
            self.app.selected.render()