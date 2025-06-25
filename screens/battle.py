from __future__ import annotations
from typing import TYPE_CHECKING
import pygame
from pygame.event import Event

from .shared import Component, Button, X, Y, S, Label
from .shared import DrawEntityList, DrawBoard, DrawEntity, DrawTile

from citadel.util import GamePhase, ActionError

if TYPE_CHECKING:
    from main import App
    from citadel.entity import Entity, EntityList
    from citadel.board import Tile


def choose_pieces(app: 'App'):
    from citadel_test import ExampleGame
    example = ExampleGame()
    example.place_lands()
    example.place_citadels()
    example.choose_personal_pieces()
    example.choose_community_pieces()
    app.game = example.game



class Battle(Component):
    '''The main battle screen.'''
    def __init__(self, app:App):
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
            "graveyard": DrawEntityList(app.game.graveyard,
                X(24), Y(0), X(144-48), Y(24), columns=6),
            }
    
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
        elif self.app.selected and isinstance(clicked, DrawTile):
            self.take_action(clicked.tile)
        elif not self.app.selected and isinstance(clicked, DrawEntity):
            self.app.selected = clicked
            self.app.selected.clickable = False
        elif not self.app.selected and isinstance(clicked, DrawTile):
            if clicked.tile.piece:
                self.app.selected = DrawEntity(clicked.tile.piece, clicked.x, clicked.y, S(12))
                self.app.selected.clickable = False
        
        if self.app.game.phase == GamePhase.END:
            print("Game over!")
    

    def take_action(self, on_tile:Tile):
        try:
            entity:Entity = self.app.selected.entity
            actions = entity.actions(on_tile, self.app.game.current_player).usable_actions()
            if len(actions) == 0:
                print(f"{entity} has no actions available on {on_tile}")
            elif len(actions) == 1:
                action = list(actions.values())[0]
                self.app.game.current_player.perform_action(entity, action.name, on_tile)
            else:
                # Show a menu or options for the player to choose an action
                print(f"Multiple actions available for {entity} on {on_tile}: {actions}")
        except ActionError as e:
            print(f"Action error: {e}")
        self.deselect()


    def deselect(self):
        self.app.selected.clickable = True
        self.app.selected = None
        for child in self.children.values():
            child.update()
    

    def render(self):
        super().render()
        if self.app.selected and isinstance(self.app.selected, DrawEntity):
            self.app.selected.render()