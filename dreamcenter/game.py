# Game Loop subroutines are imported at bottom of file
import math
import pygame as pg
import os
import time
import json
from dreamcenter.loader import import_image, import_sound, import_level
from dataclasses import dataclass, field
from dreamcenter.game_state import GameState, StateError
from dreamcenter.constants import (
    DESIRED_FPS,
    SCREENRECT,
    SPRITES,
    IMAGE_SPRITES,
)
from dreamcenter.helpers import (
    tile_positions,
    connection_match_builder,
    create_tile_map,
)
from dreamcenter.sprites import (
    Background,
)


@dataclass
class DreamGame:
    screen: pg.Surface
    screen_rect: pg.Rect
    fullscreen: bool
    state: GameState
    channels: dict
    game_menu: "GameLoop" = field(init=False, default=None)
    game_edit: "GameLoop" = field(init=False, default=None)
    game_play: "GameLoop" = field(init=False, default=None)
    game_over: "GameLoop" = field(init=False, default=None)

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
                self.game_edit.try_open_level()
                self.game_edit.loop()
            elif self.state == GameState.game_playing:
                # Pass control to active game
                self.game_play.generate_map()
                self.game_play.change_level()
                self.game_play.loop()
            elif self.state == GameState.game_over:
                # Pass control to pause menu
                self.game_over.loop()
        self.quit()

    @staticmethod
    def quit():
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
        self.screen = pg.display.set_mode(self.screen_rect.size, window_style, bit_depth)
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
        connection_match_builder()
        self.game_menu = GameMenu.create(self, IMAGE_SPRITES[(False, False, "background")])
        self.game_play = GamePlaying.create(self)
        self.game_edit = GameEditing.create(self)
        self.game_over = GameOver.create(self, IMAGE_SPRITES[(False, False, "game_over_splash")])
        self.set_state(GameState.initialized)


@dataclass
class GameLoop:
    game: DreamGame

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.set_state(GameState.quitting)
            self.handle_event(event)

    def loop(self):
        while self.state != GameState.quitting:
            self.handle_events()

    def handle_event(self, event):
        """
        Handles a singular event, `event`.
        """

    # Shortcut
    def set_state(self, new_state):
        self.game.set_state(new_state)

    @property
    def screen(self):
        return self.game.screen

    @property
    def state(self):
        return self.game.state

    @property
    def mouse_position(self):
        return pg.mouse.get_pos()


def start_game():
    game = DreamGame.create()
    game.start_game()


def create_background_tile_map(raw_tile_map):
    """
    Creates a background tile map given a raw tile map sourced from a level save file.
    """
    background_tiles = create_tile_map()
    for (y, x, dx, dy) in tile_positions():
        raw_tile = raw_tile_map[y][x]
        background_tile = Background.create_from_sprite(
            groups=[],
            index=raw_tile["index"],
            orientation=raw_tile["orientation"],
        )
        background_tile.rect.topleft = (dx, dy)
        background_tiles[y][x] = background_tile
    return background_tiles


def save_level(tile_map, shrubs, enemies, file_obj=None, return_directly=False):
    """
    Saves `tile_map` and `shrubs` to file_obj. No other sprite types (turrets, etc.) are saved.
    """
    output_map = create_tile_map()
    # This is the default format for the file. If you change it, you
    # must ensure the loader is suitably updated also.
    data = {"background": None, "shrub": None, "enemies": None}
    for (y, x, _, _) in tile_positions():
        bg_tile = tile_map[y][x]
        assert isinstance(
            bg_tile, Background
        ), f"Must be a Background tile object and not a {bg_tile}"
        output_map[y][x] = {"index": bg_tile.index, "orientation": bg_tile.orientation}
    data["background"] = output_map
    output_shrubs = []
    output_enemies = []
    for shrub in shrubs:
        output_shrubs.append(
            {
                "index": shrub.index,
                "position": shrub.rect.center,
                "orientation": shrub.orientation,
            }
        )
    data["shrubs"] = output_shrubs
    for enemy in enemies:
        output_enemies.append(
            {
                "index": enemy.index,
                "position": enemy.rect.center,
                "orientation": enemy.orientation,
            }
        )
    data["enemies"] = output_enemies
    if return_directly:
        return data
    file_obj.write(json.dumps(data))


from dreamcenter.game_play import GamePlaying
from dreamcenter.game_menu import GameMenu
from dreamcenter.game_over import GameOver
from dreamcenter.game_edit import GameEditing
