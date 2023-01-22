import pygame as pg
from dataclasses import dataclass
from pygame import Vector2 as Vector
from dreamcenter.menu_group import MenuGroup
from dreamcenter.game import GameLoop
from dreamcenter.game_state import GameState
from dreamcenter.helpers import create_surface
from dreamcenter.constants import IMAGE_SPRITES, DESIRED_FPS
from dreamcenter.sprites import Background


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
        background.blit(IMAGE_SPRITES[(False, False, "background")], (0, 0))
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
            self.screen.blit(background, (0, 0))
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
