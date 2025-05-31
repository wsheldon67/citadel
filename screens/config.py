import pygame
from pygame.event import Event
from typing import TYPE_CHECKING

from .shared import Component, Button, NumberPicker, X, Y, S

from citadel.game import Game

if TYPE_CHECKING:
    from main import App


class ConfigScreen(Component):
    '''Class for the configuration screen'''
    def __init__(self, app:'App'):
        S.app = app
        self.app = app
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
        clicked = self.app.get_component_at_position(event.pos, self)
        if clicked is None:
            return
        for name, child in self.children.items():
            if isinstance(child, NumberPicker) and clicked in child.children.values():
                self.pickers[name][0] = child.get_value(event)
        
        if clicked == self.children["Continue"]:
            print("Continue clicked")
            from .land_placement import LandPlacement
            self.app.game = Game(
                self.pickers["Number of Players"][0],
                self.pickers["Lands per Player"][0],
                self.pickers["Personal Pieces per Player"][0],
                self.pickers["Community Pieces per Player"][0],
                )
            self.app.current_screen = LandPlacement(self.app)