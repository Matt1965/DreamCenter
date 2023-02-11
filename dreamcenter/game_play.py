import pygame as pg
import random
from pygame import Vector2 as Vector
import json
from pathfinding.core.grid import Grid
from dreamcenter.loader import import_level
from dataclasses import dataclass, field
from typing import Optional, List
from dreamcenter.map_logic import Map
from dreamcenter.path_finding import define_grid
from dreamcenter.player_group import PlayerGroup
from dreamcenter.enemy_group import EnemyGroup
from dreamcenter.text_group import TextGroup
from dreamcenter.game_state import GameState
from dreamcenter.game import GameLoop
from dreamcenter.game import save_level, create_background_tile_map
from dreamcenter.sprites import SpriteManager
from dreamcenter.constants import (
    DESIRED_FPS,
    IMAGE_SPRITES,
    MOUSE_RIGHT,
    MOUSE_LEFT,
    WALLS,
    DOORS,
    CONNECTION_MATCH,
    LEVEL_CONNECTIONS,
    ALLOWED_BUFFS,
    DEBRIS,
)
from dreamcenter.helpers import (
    create_surface,
    tile_positions,
    create_tile_map,
    collide_mask,
)
from dreamcenter.enumeration import (
    Layer,
    AnimationState,
    MovementType,
)


@dataclass
class GamePlaying(GameLoop):
    layers: pg.sprite.LayeredUpdates
    level: Optional[list]
    background: pg.Surface
    map_display: pg.Surface
    sprite_manager: SpriteManager
    player_group: PlayerGroup
    enemy_group: EnemyGroup
    text_group: TextGroup
    pathfinding_grid: []
    map_manager: Map
    show_map: bool
    level_position: List[int] = field(default_factory=lambda: [19, 19])

    @classmethod
    def create(cls, game):
        layers = pg.sprite.LayeredUpdates()
        return cls(
            game=game,
            background=create_surface(),
            map_display=create_surface(IMAGE_SPRITES[(False, False, "map_display")].get_size()),
            layers=layers,
            level=None,
            map_manager=Map(),
            pathfinding_grid=None,
            show_map=False,
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
            enemy_group=EnemyGroup(
                sprite_manager=SpriteManager(
                    sprites=pg.sprite.LayeredUpdates(),
                    layers=layers,
                    indices=None,
                ),
                player=None,
            ),
            text_group=TextGroup(
                sprite_manager=SpriteManager(
                    sprites=pg.sprite.LayeredUpdates(),
                    layers=layers,
                    indices=None,
                )
            ),
        )

    def __post_init__(self):
        self.player_group.spawn_player()
        self.player_group.spawn_default_hearts()

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

    def generate_map(self):
        self.map_manager.generate_map()

    def determine_level(self) -> None:
        """
        Uses the map_logic grid to determine the level being moved into
        If the level has been previously visited it will have a saved state in "saved_state" of the grid
        """
        if self.map_manager.map_grid[self.level_position[0]][self.level_position[1]]["saved_state"]:
            data = self.map_manager.map_grid[self.level_position[0]][self.level_position[1]]["saved_state"]
            self.load_level(
                background=data["background"],
                shrubs=data["shrubs"],
                enemies=data["enemies"],
                traps=data["traps"],
                buffs=data["buffs"],
                items=data["items"],
            )
        else:
            level = self.map_manager.map_grid[self.level_position[0]][self.level_position[1]]["level"]
            self.open_level(import_level(level + ".json"))

    def change_level(self, direction="start"):
        previous_position = self.map_manager.map_grid[self.level_position[0]][self.level_position[1]]["position"]

        match direction:
            case "up":
                self.level_position[0] -= 1
                self.player_group.player.position += Vector([0, 855])
            case "down":
                self.level_position[0] += 1
                self.player_group.player.position += Vector([0, -855])
            case "left":
                self.level_position[1] -= 1
                self.player_group.player.position += Vector([1450, 0])
            case "right":
                self.level_position[1] += 1
                self.player_group.player.position += Vector([-1450, 0])
            case "start":
                pass

        if direction != "start":
            self.map_manager.map_grid[previous_position[0]][previous_position[1]]["saved_state"] = save_level(
                self.level,
                self.layers.get_sprites_from_layer(Layer.shrub.value),
                self.layers.get_sprites_from_layer(Layer.enemy.value),
                self.layers.get_sprites_from_layer(Layer.trap.value),
                self.layers.get_sprites_from_layer(Layer.buff.value),
                self.layers.get_sprites_from_layer(Layer.item.value),
                return_directly=True,
            )
        self.determine_level()

    def open_level(self, file_obj):
        data = json.loads(file_obj.read())
        self.load_level(
            background=data["background"],
            shrubs=data["shrubs"],
            enemies=data["enemies"],
            traps=data["traps"],
            buffs=data["buffs"],
            items=data["items"],
        )

    def load_level(self, background, shrubs, enemies, traps, buffs, items):
        """
        Given a valid tile map of `background` tiles, and a list
        of `shrubs`, load them into the game and reset the game.
        """
        self.curated_sprite_removal()
        self.level = create_background_tile_map(background)
        self.draw_background()
        for shrub in shrubs:
            if shrub["index"] in DEBRIS:
                self.sprite_manager.select_sprites(
                    self.sprite_manager.create_debris(
                        position=shrub["position"],
                        orientation=shrub["orientation"],
                        index=shrub["index"],
                    )
                )
            else:
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
        for buff in buffs:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_buff(
                    position=buff["position"],
                    target=self.player_group.player,
                    index=random.choice(ALLOWED_BUFFS) if buff["index"] == "random" else buff["index"],
                )
            )
            self.sprite_manager.place(buff["position"])
        for trap in traps:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_trap(
                    position=trap["position"],
                    orientation=trap["orientation"],
                    index=trap["index"],
                )
            )
            self.sprite_manager.place(trap["position"])
        for item in items:
            self.sprite_manager.select_sprites(
                self.sprite_manager.create_item(
                    position=item["position"],
                    index=item["index"],
                    target=self.player_group.player,
                )
            )
            self.sprite_manager.place(item["position"])
        if self.pathfinding_grid:
            Grid.cleanup(self.pathfinding_grid)
        if self.enemy_group.obstacles:
            self.enemy_group.clear_entities()
        self.enemy_group.add_entities(
            self.layers.get_sprites_from_layer(Layer.enemy),
            self.layers.get_sprites_from_layer(Layer.wall),
            self.player_group.player,
            self.pathfinding_grid
        )
        self.pathfinding_grid = define_grid(self.level)
        self.text_group.define_initial_texts()

    def create_blank_level(self):
        """
        Creates a blank level with a uniform tile selection.
        """
        self.load_level(create_tile_map({"index": "blank", "orientation": 0}), [])

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.layers.update()
        self.layers.draw(self.screen)
        if self.show_map:
            self.display_map()

    def display_map(self):
        position = self.map_manager.map_grid[self.level_position[1]][self.level_position[0]]["position"]
        starting_corner = (
            self.map_display.get_bounding_rect().center[1] - (position[1] * 90) - 25,
            self.map_display.get_bounding_rect().center[0] - (position[0] * 90)
        )

        self.map_display.blit(IMAGE_SPRITES[(False, False, "map_display")], (0, 0))
        for row in self.map_manager.map_grid:
            for tile in row:
                if tile["level"] == "blank":
                    continue
                connection = LEVEL_CONNECTIONS[tile["level"]]["connection"]
                self.map_display.blit(
                    CONNECTION_MATCH[connection],
                    (
                        starting_corner[1] + (tile["position"][1] * 90) - 45,
                        starting_corner[0] + (tile["position"][0] * 90) - 45
                    )
                )
        self.map_display.blit(IMAGE_SPRITES[(False, False, "map_you_are_here")], (525, 282))
        self.screen.blit(self.map_display, (370, 190))
        self.screen.blit(IMAGE_SPRITES[(False, False, "map_border")], (300, 125))

    def update_text_values(self):
        for item in self.text_group.text_sprites:
            match item.text_type:
                case "money":
                    item.set_text(f"Fragments: {self.player_group.player.money}")
                case _:
                    pass

    def loop(self):
        loop_counter = 0
        clock = pg.time.Clock()
        text_layer = pg.sprite.Group(*self.text_group.text_sprites)

        while self.state == GameState.game_playing:
            text_layer.update()
            self.update_text_values()
            self.handle_events()
            self.handle_collision()
            if loop_counter % 10 == 0:
                self.enemy_group.update()
            self.player_group.update()
            self.draw()
            text_layer.draw(self.screen)
            self.game_over_check()
            pg.display.flip()
            clock.tick(DESIRED_FPS)
            pg.display.set_caption(f"FPS {round(clock.get_fps())}")
            loop_counter += 1
        self.layers.empty()

    def handle_event(self, event):
        keys = pg.key.get_pressed()
        if keys[pg.K_ESCAPE]:
            pass
        if keys[pg.K_w]:
            self.player_group.movement_directions["top"] = True
        if keys[pg.K_s]:
            self.player_group.movement_directions["bottom"] = True
        if keys[pg.K_a]:
            self.player_group.movement_directions["left"] = True
        if keys[pg.K_d]:
            self.player_group.movement_directions["right"] = True
        if keys[pg.K_p]:
            self.set_state(GameState.main_menu)
        if keys[pg.K_TAB]:
             self.show_map = True
        if event.type == pg.KEYUP:
            if event.key == pg.K_w:
                self.player_group.movement_directions["top"] = False
            if event.key == pg.K_s:
                self.player_group.movement_directions["bottom"] = False
            if event.key == pg.K_a:
                self.player_group.movement_directions["left"] = False
            if event.key == pg.K_d:
                self.player_group.movement_directions["right"] = False
            if event.key == pg.K_TAB:
                self.show_map = False
        if event.type == pg.MOUSEBUTTONDOWN and event.button in (MOUSE_LEFT, MOUSE_RIGHT):
            if event.button == MOUSE_LEFT:
                self.player_group.firing = True
        if event.type == pg.MOUSEBUTTONUP and event.button in (MOUSE_LEFT, MOUSE_RIGHT):
            if event.button == MOUSE_LEFT:
                self.player_group.firing = False

    def handle_collision(self):
        self.collision_wall_projectile()
        self.collision_player_wall()
        self.collision_enemy_projectile()
        self.collision_enemy_wall()
        self.collision_player_enemy()
        self.collision_enemy_enemy()
        self.collision_player_door()
        self.collision_item_item()
        self.collision_player_item()
        self.collision_player_buff()
        self.collision_projectile_debris()
        self.collision_player_debris()

    def collision_wall_projectile(self):
        walls = self.layers.get_sprites_from_layer(Layer.wall)
        projectiles = self.layers.get_sprites_from_layer(Layer.projectile)
        for walls, projectiles in collide_mask(walls, projectiles):
            for projectile in projectiles:
                projectile.animation_state = AnimationState.exploding

    def collision_player_wall(self):
        player = self.layers.get_sprites_from_layer(Layer.player)
        walls = self.layers.get_sprites_from_layer(Layer.wall)
        for player, walls in collide_mask(player, walls, collide_type=None):
            for wall in walls:
                if wall.rect.collidepoint(player.rect.center):
                    self.player_group.movement_directions["top"] = False
                if wall.rect.collidepoint(player.rect.midbottom):
                    self.player_group.movement_directions["bottom"] = False
                if wall.rect.collidepoint((player.rect.midleft[0], player.rect.midleft[1] + player.rect.height / 4)):
                    self.player_group.movement_directions["left"] = False
                if wall.rect.collidepoint((player.rect.midright[0], player.rect.midright[1] + player.rect.height / 4)):
                    self.player_group.movement_directions["right"] = False

    def collision_enemy_projectile(self):
        projectiles = self.layers.get_sprites_from_layer(Layer.projectile)
        enemies = self.layers.get_sprites_from_layer(Layer.enemy)
        for enemies, projectiles in collide_mask(enemies, projectiles):
            for enemy in [enemies]:
                for projectile in projectiles:
                    if projectile.animation_state == AnimationState.stopped:
                        enemy.health -= projectile.damage
                    if enemy.animation_state != AnimationState.dying:
                        projectile.animation_state = AnimationState.exploding

    def collision_enemy_wall(self):
        enemies = self.layers.get_sprites_from_layer(Layer.enemy)
        walls = self.layers.get_sprites_from_layer(Layer.wall)
        for enemies, walls in collide_mask(enemies, walls):
            for enemy in [enemies]:
                if enemy.path is None:
                    continue
                if enemy.currently_pathfinding:
                    continue
                if enemy.movement in (MovementType.chase, MovementType.ranged_chase):
                    enemy.path = self.enemy_group.find_pathfinding_path(
                        enemy.rect.center,
                        self.player_group.player.rect.center,
                        self.pathfinding_grid,
                        enemy.speed,
                    )
                    enemy.animation_state = AnimationState.walking
                    enemy.currently_pathfinding = True
                    enemy.final_position = self.player_group.player.rect.center
                if enemy.movement in (MovementType.wander_chase, MovementType.wander):
                    enemy.path = None
                    enemy.move(enemy.previous_position)
                    enemy.movement_cooldown_remaining = 0

    def collision_player_enemy(self):
        enemies = self.layers.get_sprites_from_layer(Layer.enemy)
        player = self.layers.get_sprites_from_layer(Layer.player)
        for player, enemies in collide_mask(player, enemies):
            for enemy in enemies:
                if player.invulnerable_remaining != 0:
                    continue
                if enemy.animation_state == AnimationState.dying:
                    continue
                player.invulnerable_remaining = player.invulnerable_cooldown
                self.player_group.take_damage(enemy.collision_damage)

    def collision_enemy_enemy(self):
        enemies = self.layers.get_sprites_from_layer(Layer.enemy)
        enemies_arranged = self.enemy_group.arrange_by_distance(enemies)
        for enemy in enemies_arranged:
            for enemy_collided in pg.sprite.spritecollide(enemy, enemies, False, collided=pg.sprite.collide_mask):
                if enemy is not enemy_collided:
                    enemy_collided.waiting = True
            enemies.remove(enemy)

    def collision_player_door(self):
        player = self.layers.get_sprites_from_layer(Layer.player)
        doors = self.layers.get_sprites_from_layer(Layer.door)
        for player, doors in collide_mask(player, doors, pg.sprite.collide_circle_ratio(.6)):
            for door in doors:
                if door.rect.center[0] < 50:
                    self.change_level("left")
                    break
                if door.rect.center[0] > 1550:
                    self.change_level("right")
                    break
                if door.rect.center[1] < 50:
                    self.change_level("up")
                    break
                if door.rect.center[1] > 950:
                    self.change_level("down")
                    break

    def collision_item_item(self):
        items = self.layers.get_sprites_from_layer(Layer.item)
        for item in items:
            for item_collided in pg.sprite.spritecollide(item, items, False, collided=pg.sprite.collide_mask):
                if item is not item_collided:
                    item_collided.random_movement(15)

    def collision_player_item(self):
        items = self.layers.get_sprites_from_layer(Layer.item)
        player = self.layers.get_sprites_from_layer(Layer.player)
        for player, items in collide_mask(player, items, pg.sprite.collide_circle_ratio(2)):
            for item in items:
                item.action()
                item.kill()

    def collision_player_buff(self):
        buffs = self.layers.get_sprites_from_layer(Layer.buff)
        player = self.layers.get_sprites_from_layer(Layer.player)
        for player, buffs in collide_mask(player, buffs):
            for buff in buffs:
                if self.player_group.player.money >= buff.cost:
                    buff.action()
                    buff.kill()
                    self.player_group.player.money -= buff.cost

    def collision_player_debris(self):
        player = self.layers.get_sprites_from_layer(Layer.player)
        debris = self.layers.get_sprites_from_layer(Layer.debris)
        for player, debris in collide_mask(player, debris):
            for debri in debris:
                debri.animation_state = AnimationState.dying

    def collision_projectile_debris(self):
        projectiles = self.layers.get_sprites_from_layer(Layer.projectile)
        debris = self.layers.get_sprites_from_layer(Layer.debris)
        for projectiles, debris in collide_mask(projectiles, debris):
            for debri in debris:
                for projectile in [projectiles]:
                    if debri.animation_state != AnimationState.dying:
                        projectile.animation_state = AnimationState.exploding
                debri.animation_state = AnimationState.dying
                self.layers.change_layer(debri, Layer.shrub)

    def game_over_check(self):
        if self.player_group.player.health <= 0:
            self.set_state(GameState.game_over)

    def curated_sprite_removal(self):
        for group in Layer:
            if group in (Layer.player, Layer.health):
                continue
            self.layers.remove_sprites_of_layer(group)
