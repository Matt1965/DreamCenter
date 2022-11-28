import pygame as pg
import enum
from dreamcenter.loader import import_image, import_sound, import_level
from dataclasses import dataclass
from dataclasses import field
from constants import (
    DESIRED_FPS,
    SCREENRECT,
    SPRITES,
    IMAGE_SPRITES
)


class GameState(enum.Enum):

    # Error state
    unknown = "unknown"
    # Pre-initialization
    starting = "starting"
    # Game engine is ready
    initialized = "initialized"
    # Map editing mode
    map_editing = "map_editing"
    # Game is active
    game_playing = "game_playing"
    # Main menu
    main_menu = "main_menu"
    # End of game screen
    game_ended = "game_ended"
    # Game is exiting
    quitting = "quitting"


class StateError(Exception):
    """
    Raised if the game is in an unexpected game state at a point
    where we expect it to be in a different state.
    """


@dataclass
class DreamGame:

    screen: pg.Surface
    screen_rect: pg.Rect
    fullscreen: bool
    state: GameState
    channels: dict
    game_menu: GameLoop = field(init=False, default=None)
    game_edit: GameEditing = field(init=False, default=None)

    @classmethod
    def create(cls, fullscreen=False):
        channels = {
            "footsteps": None
        }
        game = cls(
            state=GameState.starting,
            screen=None,
            screen_rect=SCREENRECT,
            fullscreen=fullscreen,
            channels=channels,
        )
        game.init()
        return game

    def set_state(self, next_state: GameState):
        self.state = next_state

    def assert_state_is(self, *expected_states: GameState):
        if self.state not in expected_states:
            raise StateError(
                f"Expected the game state to be one of {expected_states} not {self.state}"
            )

    def loop(self):
        while self.state != GameState.quitting:
            if self.state == GameState.main_menu:
                # Pass control to game menu's loop
                self.game_menu.loop()
            elif self.state == GameState.map_editing:
                # Pass control to level editor
                self.game_edit.loop()
            elif self.state == GameState.game_playing:
                pass # Pass control to active game
        self.quit()

    def quit(self):
        pg.quit()

    def start_game(self):
        self.assert_state_is(GameState.initialized)
        self.set_state(GameState.main_menu)
        self.loop()

    def init(self):
        self.assert_state_is(GameState.starting)
        pg.init()
        window_style = pg.FULLSCREEN if self.fullscreen else 0
        bit_depth = pg.display.mode_ok(self.screen_rect.size, window_style, 32)
        screen = pg.display.set_mode(self.screen_rect.size, window_style, bit_depth)
        for sprite_index, sprite_name in SPRITES.items():
            img = import_image(sprite_name)
            for flipped_x in (True, False):
                for flipped_y in (True, False):
                    new_img = pg.transform.flip(img, flip_x=flipped_x, flip_y=flipped_y)
                    IMAGE_SPRITES[(flipped_x, flipped_y, sprite_index)] = new_img
        pg.mixer.pre_init(
            frequency=44100,
            size=32,
            channels=2,
            buffer=512,
        )
        for channel_id, channel_name in enumerate(self.channels):
            self.channels[channel_name] = pg.mixer.Channel(channel_id)
            self.channels[channel_name].set_volume(1.0)
        pg.font.init()
        self.game_menu = GameMenu(game=self)
        self.set_state(GameState.initialized)
        return screen


@dataclass
class GameLoop:
    game: DreamGame

    def handle_events(self):
        for event in pg.event.get():
            if (
                event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
            ) or event.type == pg.QUIT:
                self.set_state(GameState.quitting)
            self.handle_event(event)

    def loop(self):
        while self.state != GameState.quitting:
            self.handle_events()

    def handle_event(self, event):
        # handles singular events

    # Shortcut
    def set_state(self, new_state):
        self.game.set_state(new_state)

    @property
    def screen(self):
        return self.game.screen

    @property
    def state(self):
        return self.game.state


class GameMenu(GameLoop):
    def loop(self):
        clock = pg.time.Clock()
        self.screen.blit(IMAGE_SPRITES[(False, False, "backdrop")], (0,0))
        while self.state == GameState.main_menu:
            self.handle_events()
            pg.display.flip()
            pg.display.set_caption(f"FPS {round(clock.get_fps())}")
            clock.tick(DESIRED_FPS)

class GameEditing(GameLoop):
    pass