import pygame as pg
import json
from dataclasses import dataclass, field
from typing import Optional
from dreamcenter.game_state import GameState
from dreamcenter.game import GameLoop
from dreamcenter.game import create_background_tile_map, save_level
from dreamcenter.constants import (
    DESIRED_FPS,
    IMAGE_SPRITES,
    KEY_BACKGROUND,
    KEY_SHRUB,
    KEY_ENEMY,
    WALLS,
    DOORS,
)
from dreamcenter.helpers import (
    create_surface,
    tile_position,
    tile_positions,
    open_dialog,
    save_dialog,
    create_tile_map,
)
from dreamcenter.sprites import (
    Layer,
    SpriteManager,
)


@dataclass
class GameEditing(GameLoop):
    background: pg.Surface
    sprite_manager: SpriteManager
    level: Optional[list]
    layers: pg.sprite.LayeredUpdates
    _last_selected_sprite: Optional[int] = field(init=False, default=None)

    @classmethod
    def create(cls, game):
        layers = pg.sprite.LayeredUpdates()
        return cls(
            game=game,
            background=create_surface(),
            level=None,
            layers=layers,
            sprite_manager=SpriteManager(
                sprites=pg.sprite.LayeredUpdates(),
                layers=layers,
                indices=None,
            ),
        )

    def create_blank_level(self):
        self.load_level(create_tile_map({"index": "blank", "orientation": 0}), [], [])

    def load_level(self, background, shrubs, enemies):
        """
        Given a valid tile map of `background` tiles, and a list
        of `shrubs`, load them into the game and reset the game.
        """
        self.layers.empty()
        self.level = create_background_tile_map(background)
        self.draw_background()
        for shrub in shrubs:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_shrub(
                    position=shrub["position"],
                    orientation=shrub["orientation"],
                    index=shrub["index"],
                )
            )
            self.sprite_manager.place(shrub["position"])
        for enemy in enemies:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_enemy(
                    position=enemy["position"],
                    orientation=enemy["orientation"],
                    index=enemy["index"],
                )
            )
            self.sprite_manager.place(enemy["position"])

    def draw_background(self):
        self.background.blit(IMAGE_SPRITES[(False, False, "edit_background")], (0, 0))
        for (y, x, dx, dy) in tile_positions():
            background_tile = self.level[y][x]
            if background_tile.index in DOORS:
                self.sprite_manager.create_door(
                    position=(dx, dy),
                    index=background_tile.index,
                    orientation=background_tile.orientation,
                )
            elif background_tile.index in WALLS:
                self.sprite_manager.create_wall(
                    position=(dx, dy),
                    index=background_tile.index,
                    orientation=background_tile.orientation,
                )
            else:
                self.sprite_manager.create_background(
                    position=(dx, dy),
                    index=background_tile.index,
                    orientation=background_tile.orientation,
                )

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.layers.update()
        self.layers.draw(self.screen)

    def loop(self):
        clock = pg.time.Clock()
        self.draw_background()

        while self.state == GameState.map_editing:
            m_x, m_y = tile_position(self.mouse_position)
            self.handle_events()
            self.draw()
            pg.display.flip()
            clock.tick(DESIRED_FPS)
        self.layers.empty()

    def handle_event(self, event):
        mouse = pg.mouse.get_pressed()
        if event.type == pg.MOUSEWHEEL:
            if self.sprite_manager.selected:
                self.sprite_manager.cycle_index()
        if event.type == pg.MOUSEMOTION:
            self.sprite_manager.move(self.mouse_position)
        if self.sprite_manager.selected:
            if mouse[0]:
                for sprite in self.sprite_manager.sprites:
                    if sprite.layer == Layer.background:
                        gx, gy = tile_position(sprite.rect.topleft)
                        self.level[gy][gx] = sprite
                    else:
                        self.sprite_manager.place(self.mouse_position)
                self.sprite_manager.empty()
                self.select_sprite(self._last_selected_sprite)
            elif mouse[1]:
                self.sprite_manager.kill()
        else:
            if mouse[1]:
                found_sprites = self.layers.get_sprites_at(self.mouse_position)
                for found_sprite in found_sprites:
                    if found_sprite.layer != Layer.background:
                        found_sprite.kill()
        # Keyboard Events
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_q:
                orientation = 90
                self.sprite_manager.increment_orientation(orientation)
            if event.key == pg.K_e:
                orientation = -90
                self.sprite_manager.increment_orientation(orientation)
            if event.key == pg.K_p:
                self.game.state = GameState.main_menu
            if event.key == pg.K_F9:
                self.try_open_level()
            elif event.key == pg.K_F5:
                self.try_save_level()
            index = event.key - pg.K_1
            self.select_sprite(index)

    def try_open_level(self):
        """
        Tries to open a level with the open dialog. If the user cancels out, do nothing.
        """
        with open_dialog() as open_file:
            if open_file is not None:
                self.open_level(open_file)
            else:
                self.create_blank_level()

    def open_level(self, file_obj):
        data = json.loads(file_obj.read())
        self.load_level(
            background=data["background"], shrubs=data["shrubs"], enemies=data["enemies"]
        )

    def select_sprite(self, index: Optional[int]):
        """
        Given an integer index (intended to correspond to the
        digit keys on the keyboard) create (and select) a sprite.

        Only some are available in `GameState.game_playing`; the rest
        is intended for the map editor.
        """
        # Skip any index that's not in the 0-9 digit range.
        if index not in range(0, 9):
            return
        self.sprite_manager.kill()
        if self._last_selected_sprite != index:
            self.sprite_manager.reset()
        self._last_selected_sprite = index
        if index == KEY_BACKGROUND:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_background(position=self.mouse_position),
                self.mouse_position,
            )
        if index == KEY_SHRUB:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_shrub(position=self.mouse_position),
                self.mouse_position,
            )
        if index == KEY_ENEMY:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_enemy(position=self.mouse_position),
                self.mouse_position,
            )

    def try_save_level(self):
        """
        Tries to save a level with the save dialog used to source the filepath.
        """
        with save_dialog() as save_file:
            if save_file is not None:
                save_level(
                    self.level,
                    self.layers.get_sprites_from_layer(Layer.shrub.value),
                    self.layers.get_sprites_from_layer(Layer.enemy.value),
                    self.layers.get_sprites_from_layer(Layer.trap.value),
                    self.layers.get_sprites_from_layer(Layer.buff.value),
                    self.layers.get_sprites_from_layer(Layer.item.value),
                    save_file,
                )