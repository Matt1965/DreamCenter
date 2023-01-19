import pygame as pg
from pygame import Vector2 as Vector
from dataclasses import dataclass
from dreamcenter.game_menu import GameMenu
from dreamcenter.game_state import GameState
from dreamcenter.constants import IMAGE_SPRITES, DESIRED_FPS
from dreamcenter.helpers import create_surface


@dataclass
class GameOver(GameMenu):
    def loop(self):
        clock = pg.time.Clock()
        background = create_surface()
        background.fill((0, 0, 0, 1))
        background.blit(IMAGE_SPRITES[(False, False, "game_over_splash")], (450, 400))
        group = pg.sprite.Group()
        menu_base_position = Vector(self.game.screen_rect.center) + Vector(0, 20)
        self.menu_group.not_selected_color = (255, 159, 10)
        self.menu_group.render_position = menu_base_position
        self.menu_group.clear()
        self.menu_group.add(
            text="New Patient",
            size=40,
            action=self.action_play,
        )
        self.menu_group.add(
            text="Return to desk",
            size=40,
            action=self.action_main_menu,
        )
        self.menu_group.add(
            text="Clock out",
            size=40,
            action=self.action_quit,
        )
        menu = pg.sprite.Group(
            *self.menu_group.items
        )
        while self.state == GameState.game_over:
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

    def action_main_menu(self):
        self.set_state(GameState.main_menu)