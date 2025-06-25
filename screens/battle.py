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
            "community_label": Label(X(24), Y(144-24), X(144-48), Y(9), "Community"),
            }