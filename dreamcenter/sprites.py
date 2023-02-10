import math
import pygame as pg
import operator
import random
from pygame import Vector2 as Vector
from dataclasses import dataclass, field
from typing import Generator, Optional, Dict
from itertools import cycle, repeat, count, accumulate
from dreamcenter.helpers import extend, angle_to
from dreamcenter.constants import (
    IMAGE_SPRITES,
    TILE_HEIGHT,
    TILE_WIDTH,
    FONT_NAME,
    FONT_SIZE,
    SOUNDS,
    ALLOWED_BG,
    ALLOWED_ENEMY,
    ANIMATIONS,
    CACHE,
    ENEMY_STATS,
    ITEM_STATS,
    ALLOWED_BUFFS,
    ALLOWED_SHRUB,
    DEBRIS,
)
from dreamcenter.enumeration import (
    AnimationState,
    SpriteState,
    MovementType,
    Layer,
)


class Sprite(pg.sprite.Sprite):
    _layer = Layer.background

    @classmethod
    def create_from_surface(
        cls,
        groups,
        surface,
        **kwargs,
    ):
        rect = surface.get_rect()
        return cls(
            groups=groups,
            image=surface,
            index=None,
            rect=rect,
            **kwargs,
        )

    @classmethod
    def create_from_sprite(
        cls,
        index,
        groups,
        sounds=None,
        image_tiles=IMAGE_SPRITES,
        orientation=0,
        flipped_x=False,
        flipped_y=False,
        **kwargs,
    ):
        image = image_tiles[(flipped_x, flipped_y, index)]
        rect = image.get_rect()
        return cls(
            image=image,
            image_tiles=image_tiles,
            index=index,
            groups=groups,
            sounds=sounds,
            rect=rect,
            orientation=orientation,
            **kwargs,
        )

    def __init__(
        self,
        groups,
        image_tiles=None,
        index=None,
        rect=None,
        image=None,
        channel=None,
        sounds=None,
        orientation=0,
        position=(0,0),
        flipped_x=False,
        flipped_y=False,
        frames=None,
        animation_state=AnimationState.stopped,
    ):
        super().__init__(groups)
        self.image = image
        self.channel = channel
        self.sounds = sounds
        self.image_tiles = image_tiles
        self.index = index
        self.rect = rect
        self.orientation = orientation
        self.flipped_x = flipped_x
        self.flipped_y = flipped_y
        self.frames = frames
        self.position = position
        self.angle = self.generate_rotation()
        self._last_angle = None
        self.final_position = position
        self.animation_state = animation_state
        if self.image is not None:
            if self.index in ALLOWED_BG:
                self.mask = pg.mask.from_surface(
                    pg.transform.scale(IMAGE_SPRITES[(False, False, "bg_mask")], self.image.get_size()))
            else:
                self.mask = pg.mask.from_surface(
                    pg.transform.scale(IMAGE_SPRITES[(False, False, "collision_mask")], self.image.get_size()))
            self.surface = self.image.copy()
            self.rotate(self.orientation)
        if self.rect is not None and position is not None:
            if self.index in ALLOWED_BG:
                self.move(position, center=False)
            else:
                self.move(position)

    def set_sprite_index(self, index):
        self.image = self.image_tiles[(self.flipped_x, self.flipped_y, index)]
        self.surface = self.image.copy()
        self.rect = self.image.get_rect(center=self.rect.center)
        if self.index in ALLOWED_BG:
            self.mask = pg.mask.from_surface(
                    pg.transform.scale(IMAGE_SPRITES[(False, False, "bg_mask")], self.image.get_size()))
        else:
            self.mask = pg.mask.from_surface(
                pg.transform.scale(IMAGE_SPRITES[(False, False, "collision_mask")], self.image.get_size())
            )
        self.index = index
        self.rotate(self.orientation)

    def move(self, position, center: bool = True):
        if center:
            self.rect.center = position
        else:
            self.rect.topleft = position

    def rotate_cache_key(self):
        return (self.flipped_x, self.flipped_y, self.index)

    def rotate(self, angle):
        if angle == self._last_angle:
            return
        try:
            k = (self.rotate_cache_key(), angle)
            new_image = CACHE[k]
        except KeyError:
            new_image = pg.transform.rotate(self.surface, angle)
            CACHE[k] = new_image
        new_rect = new_image.get_rect(center=self.rect.center)
        self.image = new_image
        self.rect = new_rect
        if self.index in ALLOWED_BG:
            self.mask = pg.mask.from_surface(
                    pg.transform.rotate(
                    pg.transform.scale(IMAGE_SPRITES[(False, False, "bg_mask")], self.image.get_size()), angle))
        else:
            self.mask = pg.mask.from_surface(
                pg.transform.scale(IMAGE_SPRITES[(False, False, "collision_mask")], self.image.get_size())
            )
        self._last_angle = angle

    def generate_rotation(self):
        return repeat(self.orientation)

    def set_orientation(self, orientation):
        """
        Updates the orientation to `orientation`.
        """
        self.orientation = orientation
        self.angle = self.generate_rotation()
        self.rotate(next(self.angle))

    def animate(self):
        if self.frames is None:
            return
        roll = self.frames.get(self.animation_state, None)
        if roll is None:
            return
        try:
            next_frame_index = next(roll)
            if next_frame_index != self.index:
                self.set_sprite_index(next_frame_index)
        except StopIteration:
            if AnimationState.state_kills_sprite(self.animation_state):
                self.kill()

    def play(self):
        if self.sounds is not None and pg.mixer and self.channel is not None:
            effect_name = next(self.sounds)
            if effect_name is not None:
                effect = SOUNDS[effect_name]
                # Do not attempt to play if the channel is busy.
                if not self.channel.get_busy():
                    self.channel.play(effect, fade_ms=10)

    def update(self):
        angle = next(self.angle)
        self.rotate(angle)
        self.animate()


class DirectedSprite(Sprite):
    """
    Subclass of `Sprite` that understands basic motion and rotation.
    """

    def __init__(
            self,
            path=None,
            state=SpriteState.unknown,
            waiting=False,
            previous_position=[0, 0],
            speed=3,
            **kwargs
    ):
        super().__init__(**kwargs)
        self.state = state
        self.path = path
        self.speed = speed
        self.waiting = waiting
        self.previous_position = previous_position

    def update(self):
        try:
            self.flip_check()
            self.animate()
            if self.path is not None:
                self.state = SpriteState.moving
                if not self.waiting:
                    self.previous_position = self.position
                    position, angle = next(self.path)
                    self.position = position
                    self.move(position)
                    self.rotate(angle + next(self.angle))
            self.play()
            self.waiting = False
        except StopIteration:
            self.path = None
            if not self.waiting:
                self.state = SpriteState.stopped

    def flip_check(self):
        """
        angle of 90 -> 270 is facing right
        angle of 270 -> 90 is facing left
        """
        if not self.final_position:
            return
        _angle = round(angle_to(Vector(self.rect.center), Vector(self.final_position)), 0)
        if _angle not in range(90, 270):
            self.flipped_x = True
        else:
            self.flipped_x = False

    def direct_movement(self, target):
        self.final_position = target
        _v1 = Vector(target)
        _v2 = Vector(self.rect.center)
        distance = int(round(math.sqrt((_v1[0]-_v2[0])**2 + (_v1[1]-_v2[1])**2)))
        vh = (_v1 - _v2).normalize() * self.speed
        self.path = zip(
            accumulate(repeat(vh, int(distance/2)), func=operator.add, initial=_v2),
            repeat(0, int(distance/2)),
        )

    def random_movement(self, interval):
        if self.path:
            return
        angle = random.randint(0, 360)
        target = (
            int(interval * math.sin(angle) + self.rect.center[0]),
            int(interval * math.cos(angle) + self.rect.center[1])
        )
        self.final_position = target
        _v1 = Vector(target)
        _v2 = Vector(self.rect.center)
        distance = int(round(math.sqrt((_v1[0]-_v2[0])**2 + (_v1[1]-_v2[1])**2)))
        vh = (_v1 - _v2).normalize() * self.speed
        self.path = zip(
            accumulate(repeat(vh, int(distance/2)), func=operator.add, initial=_v2),
            repeat(0, int(distance/2)),
        )


class Text(DirectedSprite):
    """
    Subclass of `DirectedSprite` that allows for rendering text in
    addition to basic directed movement.

    Can optionally store an `action` that represents an action to be
    taken if the item is invoked somehow.
    """

    def __init__(
            self,
            text,
            color,
            size,
            text_type=None,
            font=FONT_NAME,
            action=None,
            path=None,
            **kwargs
    ):
        self.color = color
        self.size = size
        self.text_type = text_type
        self.font = font
        self.action = action
        self.rect = pg.Rect(0, 0, 0, 0)
        self.set_text(text)
        super().__init__(path=path, image=self.image, rect=self.rect, **kwargs)

    def rotate_cache_key(self):
        """
        Returns a tuple of fields used as a cache key to speed up rotations
        """
        return (
            self.flipped_x,
            self.flipped_y,
            self.index,
            self.text,
            self.size,
        )

    def set_text(self, text):
        self.text = text
        self.render_text()

    def render_text(self):
        pg_font = pg.font.Font(self.font, self.size)
        self.image = pg_font.render(self.text, True, self.color)
        self.surface = self.image
        self.rect = self.image.get_rect(center=self.rect.center)


class Projectile(DirectedSprite):
    """
    Background subclass that changes the layer to `Layer.projectile`
    """

    _layer = Layer.projectile

    def __init__(self, damage=5, **kwargs):
        self.damage = damage
        super().__init__(**kwargs)

    def update(self):
        super().update()
        if self.state == SpriteState.stopped:
            self.animation_state = AnimationState.exploding
        if self.animation_state == AnimationState.exploding:
            self.path = None


class Item(DirectedSprite):
    _layer = Layer.item

    def __init__(
        self,
        base_index=str,
        target=None,
        action=None,
        value=1,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.base_index = base_index
        self.target = target
        self.action = action
        self.value = value

    def action_sorter(self):
        match self.base_index:
            case "money":
                self.action = self.action_money
            case "health":
                self.action = self.action_health
            case _:
                pass

    def action_money(self):
        self.target.money += self.value

    def action_health(self):
        self.target.health += self.value

    def update(self):
        super().update()
        if not self.action:
            self.action_sorter()


class Buff(DirectedSprite):
    _layer = Layer.buff

    def __init__(
        self,
        item_type=str,
        target=None,
        action=None,
        cost=0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.item_type = item_type
        self.target = target
        self.action = action
        self.cost = cost

    def action_sorter(self):
        match self.index:
            case "buff_nova":
                self.action = self.action_nova
            case "buff_accumen":
                self.action = self.action_accumen
            case "buff_intuitus":
                self.action = self.action_intuitus
            case "buff_pax":
                self.action = self.action_pax
            case "buff_corpus":
                self.action = self.action_corpus
            case _:
                pass

    def action_nova(self):
        self.target.damage += 1
        self.target.cooldown += 1

    def action_accumen(self):
        if self.target.cooldown >= 0:
            self.target.cooldown -= 1
        self.target.range -= 1

    def action_intuitus(self):
        self.target.range += 1
        self.target.speed -= 1

    def action_pax(self):
        self.target.speed += 1
        self.target.health -= 1

    def action_corpus(self):
        self.target.health += 1
        self.target.damage -= 1

    def update(self):
        super().update()
        if not self.action:
            self.action_sorter()


class Enemy(DirectedSprite):
    _layer = Layer.enemy

    def __init__(
        self,
        health: int = 100,
        cooldown=100,
        cooldown_remaining=0,
        aggro_distance=500,
        collision_damage=1,
        value=1,
        destination=[0, 0],
        movement=MovementType.chase,
        movement_cooldown=0,
        movement_cooldown_remaining=0,
        **kwargs
    ):
        # Tracks the offset, if any, if the image is flipped
        self.sprite_offset = Vector(0, 0)
        self.health = health
        self.cooldown = cooldown
        self.cooldown_remaining = cooldown_remaining
        self.aggro_distance = aggro_distance
        self.collision_damage = collision_damage
        self.value = value
        self.destination = destination
        self.movement = movement
        self.movement_cooldown = movement_cooldown
        self.movement_cooldown_remaining = movement_cooldown_remaining
        super().__init__(**kwargs)

    def update(self):
        super().update()
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
        if not self.path and self.movement_cooldown_remaining > 0:
            self.movement_cooldown_remaining -= 1
        if not self.path and self.animation_state != AnimationState.dying:
            self.animation_state = AnimationState.stopped
            self.currently_pathfinding = False


class Player(Sprite):

    _layer = Layer.player

    def __init__(
        self,
        cooldown=20,
        max_health=8,
        health=8,
        damage=25,
        cooldown_remaining=0,
        position=[800, 500],
        speed=8,
        range=300,
        state=SpriteState.unknown,
        invulnerable_remaining=0,
        invulnerable_cooldown=40,
        money=0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.state = state
        self.max_health = max_health
        self.health = health
        self.damage = damage
        self.cooldown = cooldown
        self.position = position
        self.speed = speed
        self.range = range
        self.cooldown_remaining = cooldown_remaining
        self.invulnerable_remaining = invulnerable_remaining
        self.invulnerable_cooldown = invulnerable_cooldown
        self.money = money

    def update(self):
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
        if self.invulnerable_remaining > 0:
            self.invulnerable_remaining -= 1
        try:
            self.animate()
        except StopIteration:
            self.state = SpriteState.stopped
        self.move(self.position)
        self.play()

    def shoot(self):
        """
        Returns True if player is capable of firing.
        """
        if self.cooldown_remaining == 0:
            self.cooldown_remaining = self.cooldown
            self.play()
            return True
        return False


class Background(Sprite):

    _layer = Layer.background

    def update(self):
        pass


class Wall(Sprite):
    _layer = Layer.wall

    def update(self):
        pass


class Door(Sprite):
    _layer = Layer.door

    def update(self):
        pass


class Trap(Sprite):
    _layer = Layer.trap

    def update(self):
        pass


class Shrub(Sprite):
    _layer = Layer.shrub

    def update(self):
        pass


class Health(Sprite):
    _layer = Layer.health

    def update(self):
        pass

class Debris(DirectedSprite):
    _layer = Layer.debris

    def __init__(
        self,
        replacement=str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.replacement = replacement

@dataclass
class SpriteManager:

    layers: pg.sprite.LayeredUpdates
    sprites: pg.sprite.LayeredUpdates
    indices: Optional[Generator[int, None, None]]
    _last_index: Optional[int] = field(init=False, default=None)
    _last_orientation: int = field(init=False, default=0)

    def create_background(self, position, orientation=None, index=None):
        self.indices = cycle(ALLOWED_BG)
        if index is None:
            index = self._last_index
        if orientation is None:
            orientation = self._last_orientation
        background = Background.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=next(self.indices) if index is None else index,
            orientation=orientation,
            position=position,
        )
        return background

    def create_wall(self, position, orientation=None, index=None):
        wall = Wall.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=index,
            orientation=orientation,
            position=position,
        )
        return wall

    def create_debris(self, position, orientation=None, index=None):
        debris = Debris.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=index,
            state=SpriteState.stopped,
            orientation=orientation,
            position=position,
            replacement=DEBRIS[index]["replacement"],
            frames=create_animation_roll(
                {
                    AnimationState.dying: extend(
                        DEBRIS[index]["anim_dying"], 12
                    ),
                }
            )
        )
        return debris

    def create_trap(self, position, orientation=None, index=None):
        trap = Trap.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=index,
            orientation=orientation,
            position=position,
        )
        return trap

    def create_door(self, position, orientation=None, index=None):
        door = Door.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=index,
            orientation=orientation,
            position=position,
        )
        return door

    def create_health(self, position, orientation=None, index=None, flipped_x=False):
        health = Health.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=index,
            orientation=orientation,
            flipped_x=flipped_x,
            position=position,
        )
        return health

    def create_item(self, position, target, index=None):
        if index:
            base_index = index.split("_")[0].lower()
        else:
            index = self._last_index
        item = Item.create_from_sprite(
            index=next(self.indices) if index is None else index,
            groups=[self.layers],
            state=SpriteState.stopped,
            position=position,
            base_index=base_index,
            target=target,
            frames=create_animation_roll(
                {
                    AnimationState.stopped: cycle(extend(
                        ITEM_STATS[base_index]["anim_stop"], 20
                    )),
                },
            )
        )
        return [item]

    def create_buff(self, position, target=None, cost=5, index=None):
        self.indices = None
        buff = Buff.create_from_sprite(
            index="random" if index is None else index,
            groups=[self.layers],
            position=position,
            target=target,
            cost=cost,
        )
        return buff

    def create_player(self, position=(800, 500)):
        player = Player.create_from_sprite(
            index="edwardo",
            groups=[self.layers],
            state=SpriteState.moving,
        )
        player.move(position)
        return player

    def create_enemy(self, position, orientation=None, index=None):
        self.indices = cycle(ALLOWED_ENEMY)
        if not index:
            index = self._last_index
            if not index:
                base_index = next(self.indices)
            else:
                base_index = index
        else:
            base_index = index.split("_")[0].lower()
        if orientation is None:
            orientation = self._last_orientation
        enemy = Enemy.create_from_sprite(
            index=next(self.indices) if index is None else index,
            groups=[self.layers],
            state=SpriteState.stopped,
            sounds=None,
            position=position,
            value=ENEMY_STATS[base_index]["value"],
            health=ENEMY_STATS[base_index]["health"],
            speed=ENEMY_STATS[base_index]["speed"],
            collision_damage=ENEMY_STATS[base_index]["collision_damage"],
            aggro_distance=ENEMY_STATS[base_index]["aggro_distance"],
            movement=ENEMY_STATS[base_index]["movement"],
            movement_cooldown=ENEMY_STATS[base_index]["movement_cooldown"],
            frames=create_animation_roll(
                {
                    AnimationState.dying: extend(
                        ENEMY_STATS[base_index]["anim_dying"], 12
                    ),
                    AnimationState.walking: cycle(extend(
                        ENEMY_STATS[base_index]["anim_walk"], 7
                    )),
                    AnimationState.stopped: cycle(extend(
                        ENEMY_STATS[base_index]["anim_stop"], 20
                    )),
                },
            ),
        )
        return enemy

    def create_shrub(self, position, orientation=None, index=None):
        """
        Factory that creates a shrub sprite at a given `position`,
        with optional `index` and `orientation`.
        """
        self.indices = cycle(ALLOWED_SHRUB)
        if not index:
            index = self._last_index
        else:
            base_index = index.split("_")[0].lower()
        if orientation is None:
            orientation = self._last_orientation
        shrub = Shrub.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=next(self.indices) if index is None else index,
            orientation=orientation,
        )
        shrub.move(position)
        return shrub

    def create_projectile(self, source, target, speed=5, max_distance=200, damage=5):
        """
        Factory that creates a projectile sprite starting at `source`
        and moves toward `target` at `speed` before disappearing if it
        reaches `max_distance`.
        """
        v1 = Vector(target)
        v2 = Vector(source)
        vh = (v1 - v2).normalize() * speed
        path = zip(
            accumulate(repeat(vh, max_distance), func=operator.add, initial=v2),
            count(random.randint(0, 180)),
        )
        for _ in range(3):
            next(path)
        projectile = Projectile.create_from_sprite(
            position=source,
            groups=[self.layers],
            orientation=0,
            index="projectile",
            damage=damage,
            frames=create_animation_roll(
                {
                    AnimationState.exploding: extend(
                        ANIMATIONS["projectile_explode"], 2
                    ),
                },
            ),
            path=path,
            sounds=None,
        )
        projectile.move(source)
        return [projectile]

    def select_sprites(self, sprites, position=None):
        self.sprites.add(sprites)
        if position is not None:
            self.move(position)

    def generate_rotation(self):
        """
        Repeats the sprite's default orientation forever.

        This is typically done only for sprites with a fixed
        orientation that never changes.
        """
        return repeat(self.orientation)

    def increment_orientation(self, relative_orientation):
        """
        Increments each sprite's relative orientation by `relative_orientation`.
        """
        for sprite in self.sprites:
            rot = sprite.orientation
            rot += relative_orientation
            rot %= 360
            sprite.set_orientation(rot)
            self._last_orientation = rot

    def move(self, position):
        x, y = position
        for sprite in self.sprites:
            if sprite.layer in (Layer.background, Layer.wall, Layer.trap, Layer.door):
                gx, gy = (x - (x % TILE_WIDTH), y - (y % TILE_HEIGHT))
                sprite.move((gx, gy), center=False)
            else:
                sprite.move((x, y))

    def place(self, position, clear_after=True):
        for sprite in self.sprites:
            sprite.move(position)
            if clear_after:
                self.sprites.remove(sprite)

    def reset(self):
        """
        Resets the last index and orientation.
        """
        self._last_index = None
        self._last_orientation = 0

    @property
    def selected(self):
        return bool(self.sprites)

    def cycle_index(self):
        """
        Cycles the index of sprites to the next one in the
        generator and updates the sprite index of all sprites
        accordingly.

        Note this only works with background and shrub sprites.
        """
        if self.indices is None:
            return
        new_index = next(self.indices)
        for sprite in self.sprites:
            sprite.set_sprite_index(new_index)
        self._last_index = new_index

    def update(self):
        """
        Pass-through to the internal sprite group's update method.
        """
        return self.sprites.update()

    def clear(self, dest, background):
        """
        Pass-through to the internal sprite group's clear method.
        """
        return self.sprites.clear(dest, background)

    def draw(self, surface):
        """
        Pass-through to the internal sprite group's draw method.
        """
        return self.sprites.draw(surface)

    def empty(self):
        """
        Pass-through to the sprite group's empty method.
        """
        self.sprites.empty()

    def kill(self):
        """
        Kills all sprites in the internal sprites group.
        """
        for sprite in self.sprites:
            sprite.kill()


def create_animation_roll(frames: Dict[AnimationState, Generator[int, None, None]]):
    """
    Takes a dictionary of animation states (as keys) and frame
    generators (as values) and fills out the missing ones with `None`.
    """
    for state in AnimationState:
        if state not in frames:
            frames[state] = None
    return frames
