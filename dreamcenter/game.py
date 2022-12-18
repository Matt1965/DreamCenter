import pygame as pg
from pygame import Vector2 as Vector
import enum
import json
import tkinter
import tkinter.filedialog
from contextlib import contextmanager
from dreamcenter.loader import import_image, import_sound, import_level
from dataclasses import dataclass, field
from typing import Optional, List
from dreamcenter.constants import (
    DESIRED_FPS,
    SCREENRECT,
    SPRITES,
    IMAGE_SPRITES,
    PLAYER_MOVE_SPEED,
    TILES_X,
    TILES_Y,
    MOUSE_RIGHT,
    MOUSE_LEFT,
    KEY_BACKGROUND,
    KEY_SHRUB,
    KEY_ENEMY,
    MOVEMENT_BLOCKED,
)
from dreamcenter.helpers import (
    create_surface,
    tile_position,
    tile_positions,
)
from dreamcenter.sprites import (
    Background,
    Sprite,
    Layer,
    SpriteManager,
    Text,
    SpriteState,
    AnimationState,
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
    game_menu: "GameLoop" = field(init=False, default=None)
    game_edit: "GameLoop" = field(init=False, default=None)
    game_play: "GameLoop" = field(init=False, default=None)

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
                self.game_play.try_open_level()
                self.game_play.loop()
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
        self.game_menu = GameMenu.create(self, IMAGE_SPRITES[(False, False, "background")])
        self.game_play = GamePlaying.create(self)
        self.game_edit = GameEditing.create(self)
        self.set_state(GameState.initialized)


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


@dataclass
class MenuGroup:

    render_position: Vector = Vector(0, 0)
    selected_color: str = "red"
    not_selected_color: str = "black"
    selected: Optional[int] = 0
    items: List[Text] = field(default_factory=list)

    def set_selected(self, index):
        """
        Sets the selected item to `index`. All menu group items
        are re-rendered and their selected colors changed to match the
        new index.
        """
        for idx, menu_item in enumerate(self.items):
            if idx == index:
                menu_item.color = self.selected_color
                self.selected = idx
            else:
                menu_item.color = self.not_selected_color
            menu_item.render_text()

    def move(self, direction):
        """
        Moves the selection in `direction`, which is either a
        positive or negative number, indicating down or up, respectively.
        """
        if self.selected is None:
            self.selected = 0
        self.selected += direction
        self.selected %= len(self.items)
        self.set_selected(self.selected)

    def forward(self):
        """
        Moves the selected menu item forward one position
        """
        self.move(1)

    def backward(self):
        """
        Moves the selected menu item backward one position
        """
        self.move(-1)

    def add_menu_item(self, *menu_items):
        """
        Adds `menu_items` to the end of the menu items list.
        """
        self.items.extend(menu_items)

    def get_menu_item_position(self):
        """
        Calculates a menu item's *center* position on the screen,
        taking into account all the other menu items' font sizes and
        line height spacing.
        """
        offset = Vector(
            0,
            sum(
                menu_item.font.get_height() + menu_item.font.get_linesize()
                for menu_item in self.items
            ),
        )
        return self.render_position + offset

    def clear(self):
        self.items.clear()

    def add(self, text, size, action):
        sprite = Text(
            groups=[],
            color=self.not_selected_color,
            text=text,
            size=size,
            action=action,
        )
        self.add_menu_item(sprite)
        v = self.get_menu_item_position()
        sprite.move(v)
        # Set the selected item to the top-most item.
        self.move(0)

    def execute(self):
        """
        Executes the action associated with the selected menu
        item. Requires that a callable is associated with the menu
        item's `action`.
        """
        assert self.selected is not None, "No menu item is selected"
        menu = self.items[self.selected]
        assert callable(
            menu.action
        ), f"Menu item {menu} does not have a callable action"
        menu.action()


@dataclass
class GameMenu(GameLoop):
    background: pg.Surface
    menu_group: MenuGroup

    @classmethod
    def create(cls, game, background):
        return cls(game=game, background=background, menu_group=MenuGroup())

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                self.menu_group.backward()
            if event.key == pg.K_DOWN:
                self.menu_group.forward()
            if event.key == pg.K_RETURN:
                self.menu_group.execute()
        if event.type == pg.MOUSEBUTTONDOWN:
            self.check_collision()

    def check_collision(self):
        for index, item in enumerate(self.menu_group.items):
            if item.rect.collidepoint(self.mouse_position):
                self.menu_group.set_selected(index)
                self.menu_group.execute()

    def action_play(self):
        self.set_state(GameState.game_playing)

    def action_edit(self):
        self.set_state(GameState.map_editing)

    def action_quit(self):
        self.set_state(GameState.quitting)

    def loop(self):
        clock = pg.time.Clock()
        background = create_surface()
        background.blit(IMAGE_SPRITES[(False, False, "background")], (0,0))
        group = pg.sprite.Group()
        menu_base_position = Vector(self.game.screen_rect.center)
        self.menu_group.render_position = menu_base_position
        self.menu_group.clear()
        logo = Background.create_from_sprite(
            groups=[group],
            index="logo",
            orientation=0,
            position=self.game.screen_rect.center,
        )
        self.menu_group.add(
            text="Start",
            size=80,
            action=self.action_play,
        )
        self.menu_group.add(
            text="Map Maker",
            size=50,
            action=self.action_edit,
        )
        self.menu_group.add(
            text="Quit",
            size=50,
            action=self.action_quit,
        )
        menu = pg.sprite.Group(
            *self.menu_group.items
        )

        while self.state == GameState.main_menu:
            self.screen.blit(background, (0,0))
            menu.draw(self.screen)
            self.handle_events()
            menu.update()
            # Instruct all sprites to update
            group.update()
            # Tell sprites where to draw
            group.draw(self.screen)
            pg.display.flip()
            pg.display.set_caption(f"FPS {round(clock.get_fps())}")
            clock.tick(DESIRED_FPS)


@dataclass
class PlayerGroup():

    sprite_manager: SpriteManager
    player = None
    up = False
    down = False
    left = False
    right = False
    firing = False

    def spawn_player(self):
        self.player = self.sprite_manager.create_player(SCREENRECT.center)

    def move_player(self):
        move = pg.math.Vector2(self.right - self.left, self.down - self.up)
        if move.length_squared() > 0:
            move.scale_to_length(PLAYER_MOVE_SPEED)
            self.player.position[0] += move[0]
            self.player.position[1] += move[1]

    def fire_projectile(self):
        if self.player.cooldown_remaining == 0 and self.firing == True:
            self.sprite_manager.create_projectile(self.player.position, pg.mouse.get_pos())
            self.player.cooldown_remaining = self.player.cooldown

    def update(self):
        self.move_player()
        self.fire_projectile()



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
        self.load_level(create_tile_map({"index": "blank", "orientation": 0}), [])

    def load_level(self, background, shrubs):
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
            self.sprite_manager.empty()

    def draw_background(self):
        self.background.blit(IMAGE_SPRITES[(False, False, "edit_background")], (0,0))

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
        if event.type == pg.MOUSEWHEEL:
            if self.sprite_manager.selected:
                self.sprite_manager.cycle_index()
        if event.type == pg.MOUSEMOTION:
            self.sprite_manager.move(self.mouse_position)
        if event.type == pg.MOUSEBUTTONDOWN and event.button in (
                MOUSE_LEFT,
                MOUSE_RIGHT,
        ):
            if self.sprite_manager.selected:
                if event.button == MOUSE_LEFT:
                    for sprite in self.sprite_manager.sprites:
                        if sprite.layer == Layer.background:
                            gx, gy = tile_position(sprite.rect.topleft)
                            self.level[gy][gx] = sprite
                        else:
                            self.sprite_manager.place(self.mouse_position)
                    self.sprite_manager.empty()
                    self.select_sprite(self._last_selected_sprite)
                elif event.button == MOUSE_RIGHT:
                    self.sprite_manager.kill()
            else:
                if event.button == MOUSE_RIGHT:
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

    def open_level(self, file_obj, show_hud: bool = True):
        data = json.loads(file_obj.read())
        self.load_level(
            background=data["background"], shrubs=data["shrubs"]
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
            self.spawn_enemy()

    def try_save_level(self):
        """
        Tries to save a level with the save dialog used to source the filepath.
        """
        with save_dialog() as save_file:
            if save_file is not None:
                save_level(
                    self.level,
                    self.layers.get_sprites_from_layer(Layer.shrub.value),
                    save_file,
                )


@dataclass
class GamePlaying(GameLoop):

    layers: pg.sprite.LayeredUpdates
    level: Optional[list]
    background: pg.Surface
    sprite_manager: SpriteManager
    player_group: PlayerGroup

    @classmethod
    def create(cls, game):
        layers = pg.sprite.LayeredUpdates()
        return cls(
            game=game,
            background=create_surface(),
            layers=layers,
            level=None,
            sprite_manager=SpriteManager(
                sprites=pg.sprite.LayeredUpdates(),
                layers=layers,
                indices=None,
            ),
            player_group=PlayerGroup(
                sprite_manager=SpriteManager(
                    sprites=pg.sprite.LayeredUpdates(),
                    layers=layers,
                    indices=None,
                ),
            ),
        )

    def draw_background(self):
        self.background.blit(IMAGE_SPRITES[(False, False, "play_background")], (0, 0))
        for (y, x, dx, dy) in tile_positions():
            background_tile = self.level[y][x]
            self.sprite_manager.create_background(
                position=(dx, dy),
                index=background_tile.index,
            )

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
            background=data["background"], shrubs=data["shrubs"]
        )

    def load_level(self, background, shrubs):
        """
        Given a valid tile map of `background` tiles, and a list
        of `shrubs`, load them into the game and reset the game.
        """
        self.layers.empty()
        self.level = create_background_tile_map(background)
        self.draw_background()
        for shrub in shrubs:
            # Use the create/select features of the sprite manager to place the shrubs.
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_shrub(
                    position=shrub["position"],
                    orientation=shrub["orientation"],
                    index=shrub["index"],
                )
            )
            self.sprite_manager.place(shrub["position"])

    def create_blank_level(self):
        """
        Creates a blank level with a uniform tile selection.
        """
        self.load_level(create_tile_map({"index": "blank", "orientation": 0}), [])

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.layers.update()
        self.layers.draw(self.screen)

    def loop(self):
        clock = pg.time.Clock()
        self.player_group.spawn_player()

        while self.state == GameState.game_playing:
            self.handle_events()
            self.handle_collision()
            self.player_group.update()
            self.draw()
            pg.display.flip()
            clock.tick(DESIRED_FPS)
        self.layers.empty()

    def handle_event(self, event):
        keys = pg.key.get_pressed()
        if keys[pg.K_w]:
            self.player_group.up = True
        if keys[pg.K_s]:
            self.player_group.down = True
        if keys[pg.K_a]:
            self.player_group.left = True
        if keys[pg.K_d]:
            self.player_group.right = True
        if event.type == pg.KEYUP:
            if event.key == pg.K_w:
                self.player_group.up = False
            if event.key == pg.K_s:
                self.player_group.down = False
            if event.key == pg.K_a:
                self.player_group.left = False
            if event.key == pg.K_d:
                self.player_group.right = False
        if event.type == pg.MOUSEBUTTONDOWN and event.button in (MOUSE_LEFT, MOUSE_RIGHT):
            if event.button == MOUSE_LEFT:
                self.player_group.firing = True
        if event.type == pg.MOUSEBUTTONUP and event.button in (MOUSE_LEFT, MOUSE_RIGHT):
            if event.button == MOUSE_LEFT:
                self.player_group.firing = False

    def handle_collision(self):
        enemies = self.layers.get_sprites_from_layer(Layer.enemy)
        tiles = self.layers.get_sprites_from_layer(Layer.background)
        projectiles = self.layers.get_sprites_from_layer(Layer.projectile)
        player = self.layers.get_sprites_from_layer(Layer.player)
        print(projectiles)
        for tiles, projectiles in collide_mask(tiles, projectiles):
            if tiles.index in MOVEMENT_BLOCKED:
                for projectile in projectiles:
                    projectile.animation_state = AnimationState.exploding

        tiles = self.layers.get_sprites_from_layer(Layer.background)
        for player, tiles in collide_mask(player, tiles):
            for tile in tiles:
                if tile.index in MOVEMENT_BLOCKED:
                    if tile.rect.collidepoint(player.rect.midtop):
                        self.player_group.up = False
                    if tile.rect.collidepoint(player.rect.midbottom):
                        self.player_group.down = False
                    if tile.rect.collidepoint(player.rect.midright):
                        self.player_group.right = False
                    if tile.rect.collidepoint(player.rect.midleft):
                        self.player_group.left = False


def start_game():
    game = DreamGame.create()
    game.start_game()


def collide_mask(group_a, group_b):
    """
    Uses the sprite mask attribute to check if two groups of sprites are colliding.
    """
    for sprite_a, sprite_b in pg.sprite.groupcollide(
        group_a,
        group_b,
        False,
        False,
        collided=pg.sprite.collide_mask,
    ).items():
        yield sprite_a, sprite_b


def create_tile_map(default_value=None) -> list:
    """
    Creates a grid tile map with default value of None
    """
    return [[default_value for _ in range(TILES_X)] for _ in range(TILES_Y)]


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


def save_level(tile_map, shrubs, file_obj):
    """
    Saves `tile_map` and `shrubs` to file_obj. No other sprite types (turrets, etc.) are saved.
    """
    output_map = create_tile_map()
    # This is the default format for the file. If you change it, you
    # must ensure the loader is suitably updated also.
    data = {"background": None, "shrub": None, "waves": None}
    for (y, x, _, _) in tile_positions():
        bg_tile = tile_map[y][x]
        assert isinstance(
            bg_tile, Background
        ), f"Must be a Background tile object and not a {bg_tile}"
        output_map[y][x] = {"index": bg_tile.index, "orientation": bg_tile.orientation}
    data["background"] = output_map
    output_shrubs = []
    for shrub in shrubs:
        output_shrubs.append(
            {
                "index": shrub.index,
                "position": shrub.rect.center,
                "orientation": shrub.orientation,
            }
        )
    data["shrubs"] = output_shrubs
    file_obj.write(json.dumps(data))


@contextmanager
def open_dialog(title="Open file...", filetypes=(("Tower Defense Levels", "*json"),)):
    """
    Context manager that yields the opened file, which could be
    None if the user exits it without selecting. If there is a file it
    is closed when the context manager exits.
    """
    try:
        f = tkinter.filedialog.askopenfile(title=title, filetypes=filetypes)
        yield f
    finally:
        if f is not None:
            f.close()

@contextmanager
def save_dialog(title="Save file...", filetypes=(("Tower Defense Levels", "*.json"),)):
    f = tkinter.filedialog.asksaveasfile(title=title, filetypes=filetypes)
    try:
        yield f
    finally:
        if f is not None:
            f.close()

