import pygame as pg
from pygame import Vector2 as Vector
import enum
from dreamcenter.loader import import_image, import_sound, import_level
from dataclasses import dataclass, field
from typing import Optional, List
from dreamcenter.constants import (
    DESIRED_FPS,
    SCREENRECT,
    SPRITES,
    IMAGE_SPRITES,
)
from dreamcenter.helpers import (
    create_surface,
    create_tile_map,
    tile_position,
    tile_positions,
)
from dreamcenter.sprites import (
    Background,
    Sprite,
    Layer,
    SpriteManager,
    Text
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
        positive or negative number, indicating down or up,
        respectively.
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
        logo = Background.create_from_tile(
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
class GameEditing(GameLoop):

    background: pg.Surface
    sprite_manager: SpriteManager
    level: Optional[list]
    layers: pg.sprite.LayeredUpdates

    def create(cls, game):
        layers = pg.sprite.LayeredUpdates
        return cls(
            game=game,
            background=create_surface(),
            level=None,
            sprite_manager=SpriteManager(
                sprites=pg.sprite.LayeredUpdates(),
                indices=None,
                layers=layers,
                channels=game.channels,
            )
        )

    def create_blank_level(self):
        self.load_level(create_tile_map({"index": "blank", "orientation": 0}), [])

    def load_level(self, background, shrubs):
        self.layers.empty()
        self.level = create_background_tile_map(background)
        self.draw_background()
        self.mode.reset()
        for shrub in shrubs:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_shrub(
                    position=shrub["position"],
                    orientation=shrub["orientation"],
                    index = shrub["index"],
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
        group = pg.sprite.Group()

        while self.state in GameState.map_editing:
            mouse_pos = pg.mouse.get_pos()
            m_x, m_y = tile_position(mouse_pos)
            self.handle_events()
            self.draw()
            pg.display.flip()
            clock.tick(DESIRED_FPS)
        self.layers.empty()

    def handle_event(self, event):
        if event.type == pg.MOUSEMOTION:
            self.sprite.move(self.mouse_position)



def start_game():
    game = DreamGame.create()
    game.start_game()


def create_background_tile_map():
    background_tiles = create_tile_map()
    for (gy, gx, x, y) in tile_positions():
        background_tile = Background.create_from_sprite(
            groups=[],
            index="blank",
        )
        background_tile.rect.topleft = (x, y)
        background_tiles[gy][gx] = background_tile
    return background_tiles

