import random
from dataclasses import dataclass, field
from typing import List
from pygame import Vector2 as Vector
from itertools import repeat
from dreamcenter.sprites import SpriteManager
from dreamcenter.helpers import get_line
from dreamcenter.enumeration import AnimationState, MovementType, Layer
from dreamcenter.path_finding import find_path, convert_path


@dataclass
class EnemyGroup:
    sprite_manager: SpriteManager
    player: None
    grid = []
    enemies: List = field(default_factory=list)
    obstacles: List = field(default_factory=list)

    def spawn_enemy(self):
        pass

    def update(self):
        for enemy in self.enemies:
            self.handle_movement(enemy)
            self.handle_death(enemy)

    def handle_movement(self, enemy):
        if enemy.movement in (MovementType.wander, MovementType.wander_chase):
            if enemy.movement_cooldown_remaining == 0:
                enemy.random_movement(enemy.speed * 10)
                if enemy.animation_state is not AnimationState.walking:
                    enemy.animation_state = AnimationState.walking
                enemy.movement_cooldown_remaining = enemy.movement_cooldown
        if enemy.movement in (MovementType.wander_chase, MovementType.chase, MovementType.ranged_chase):
            if self.in_sight(enemy, self.player):
                enemy.direct_movement(self.player.rect.center)
                if enemy.animation_state is not AnimationState.walking:
                    enemy.animation_state = AnimationState.walking

    def handle_death(self, enemy):
        if enemy.health <= 0:
            enemy.path = None
            self.handle_drops(enemy)
            enemy.animation_state = AnimationState.dying
            self.enemies.remove(enemy)

    def in_sight(self, enemy, target):
        line_of_sight = get_line(enemy.rect.center, target.rect.center)

        if Vector(line_of_sight[0]).distance_to(line_of_sight[-1]) > enemy.aggro_distance:
            return False

        obstacle_list = [obstacle.rect for obstacle in self.obstacles]
        zone = enemy.rect.inflate(enemy.aggro_distance * 2, enemy.aggro_distance * 2)
        obstacles_in_sight = zone.collidelistall(obstacle_list)

        for x in range(1, len(line_of_sight), 5):
            for obs_index in obstacles_in_sight:
                if obstacle_list[obs_index].collidepoint(line_of_sight[x]):
                    return False

        return True

    def add_entities(self, enemies, obstacles, player, grid):
        for enemy in enemies:
            self.enemies.append(enemy)
        for obstacle in obstacles:
            self.obstacles.append(obstacle)
        self.player = player
        self.grid = grid

    def clear_entities(self):
        self.obstacles.clear()
        self.enemies.clear()

    def handle_drops(self, enemy):
        for _ in range(random.randint(0, enemy.value)):
            self.sprite_manager.create_item(
                index="money",
                position=enemy.rect.center,
                target=self.player
            )

    def arrange_by_distance(self, group):
        order = {}
        for entity in group:
            distance = Vector(entity.rect.center).distance_to(Vector(self.player.rect.center))
            order.update({entity: distance})
        return list(dict.keys({k: v for k, v in sorted(order.items(), key=lambda item: item[1])}))

    @staticmethod
    def find_pathfinding_path(position, target, grid, speed):
        grid_path = find_path(position, target, grid)

        return zip(convert_path(grid_path, speed), repeat(0))