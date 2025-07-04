from __future__ import annotations
from typing import TYPE_CHECKING
import pygame
from pygame.event import Event

from .shared import Component, Button, X, Y, S, Label
from .shared import DrawEntityList, DrawBoard, DrawEntity

from citadel.util import GamePhase, ActionError

if TYPE_CHECKING:
    from main import App
    from citadel.entity import Entity, EntityList


def place_lands(app:'App'):
    from citadel_test import ExampleGame
    example = ExampleGame()
    example.place_lands()
    example.place_citadels()
    app.game = example.game


class PieceSelection(Component):
    '''The piece selection screen.'''
    def __init__(self, app:'App'):
        super().__init__()
        self.app = app
        self.children = {
            "board": DrawBoard(app.game.board, X(72), Y(72), X(144-36), Y(144-36)),
            "player0": DrawEntityList(app.game.players[0].personal_stash,
                X(144-24), Y(9), X(24), Y(144)),
            "player0_label": Label(X(144-24), Y(0), X(24), Y(9), "Player 1"),
            "player1": DrawEntityList(app.game.players[1].personal_stash,
                X(0), Y(9), X(24), Y(144)),
            "player1_label": Label(X(0), Y(0), X(24), Y(9), "Player 2"),
            "community": DrawEntityList(app.game.community_pool,
                X(24), Y(144-24), X(144-48), Y(24), columns=6),
            "community_label": Label(X(24), Y(144-24), X(144-48), Y(9), "Community"),
            "piece_picker": DrawEntityList(app.game.available_pieces,
                X(24), Y(0), X(144-48), Y(24), columns=6),
            }
        self.children["player0"].clickable = True
        self.children["player1"].clickable = True
        self.children["community"].clickable = True


    def handle_event(self, event:Event):
        if event.type == pygame.MOUSEMOTION:
            self.on_mouse_motion(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.on_click(event)


    def on_mouse_motion(self, event:Event):
        if self.app.selected and isinstance(self.app.selected, DrawEntity):
            self.app.selected.x = X(float(event.pos[0] / self.app.w * 144) - self.app.selected.s / 2)
            self.app.selected.y = Y(float(event.pos[1] / self.app.h * 144) - self.app.selected.s / 2)


    def on_click(self, event:Event):
        clicked = self.app.get_component_at_position(event.pos)
        if self.app.selected and clicked is None:
            self.deselect()
        elif self.app.selected and isinstance(clicked, DrawEntityList):
            self.choose_piece(clicked.entities)
        elif not self.app.selected and isinstance(clicked, DrawEntity):
            self.app.selected = clicked
            self.app.selected.clickable = False
        
        if all([player.is_done_choosing_pieces for player in self.app.game.players]):
            from .battle import Battle
            self.app.game.phase = GamePhase.BATTLE
            self.app.current_screen = Battle(self.app)
    

    def choose_piece(self, location:EntityList):
        selected_entity:Entity = self.app.selected.entity
        try:
            if location.name == "Community Pool":
                self.app.game.current_player.choose_community_piece(selected_entity.__class__)
            elif location == self.app.game.current_player.personal_stash:
                self.app.game.current_player.choose_personal_piece(selected_entity.__class__)
            else:
                return
        except ValueError as e:
            print(e)
            return
        self.app.game.end_turn()
        self.app.selected = None
        for child in self.children.values():
            child.update()
    

    def deselect(self):
        self.app.selected.clickable = True
        self.app.selected = None
        for child in self.children.values():
            child.update()