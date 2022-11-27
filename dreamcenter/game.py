import pygame as pg
from dataclasses import dataclass
from constants import (
    DESIRED_FPS,
    SCREENRECT
)

def start_game():
    init(pg.Rect(0, 0, 1024, 768))

@dataclass
class DreamGame:

    screen: pg.Surface
    screen_rect: pg.Rect
    fullscreen: bool

    @classmethod
    def create(cls, fullscreen=False):
        game = cls(
            screen=None,
            screen_rect=SCREENRECT,
            fullscreen=fullscreen
        )
        game.init()
        return

    def loop(self):
        pass

    def quit(self):
        pg.quit()

    def start_game(self):
        self.loop()

    def init(self):
        pg.init()
        window_style = pg.FULLSCREEN if self.fullscreen else 0
        bit_depth = pg.display.mode_ok(self.screen_rect.size, window_style, 32)
        screen = pg.display.set_mode(self.screen_rect.size, window_style, bit_depth)
        pg.mixer.pre_init(
            frequency=44100,
            size=32,
            channels=2,
            buffer=512,
        )
        pg.font.init()
        return screen
