import enum
import math
import pygame as pg
import operator
import random
from pygame import Vector2 as Vector
from dataclasses import dataclass, field
from typing import Generator, Optional, Dict
from itertools import cycle, repeat, count, accumulate
from dreamcenter.helpers import extend
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
)


class AnimationState(enum.Enum):
    """
    Possible animation states
    """
    stopped = "stopped"
    walking = "walking"
    dying = "dying"
    exploding = "exploding"

    @classmethod
    def state_kills_sprite(cls, state):
        """
        Returns true when in a state that should kill sprite upon completion
        """
        return state in (cls.exploding, cls.dying)


class SpriteState(enum.Enum):

    """
    Possible states for movable sprites (like enemies)
    """
    unknown = "unknown"
    moving = "moving"
    stopped = "stopped"


class Layer(enum.IntEnum):

    background = 0
    wall = 20
    enemy = 40
    shrub = 50
    trap = 60
    player = 70
    projectile = 90


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
        self.angle = self.generate_rotation()
        self._last_angle = None
        self._final_position = None
        self.animation_state = animation_state
        if self.image is not None:
            if self.index in ALLOWED_BG:
                self.mask = pg.mask.from_surface(self.image)
            else:
                self.mask = pg.mask.from_surface(
                    pg.transform.scale(IMAGE_SPRITES[(False, False, "collision_mask")], self.image.get_size())
                    )
            self.surface = self.image.copy()
            self.rotate(self.orientation)
        if self.rect is not None and position is not None:
            self.move(position)

    def set_sprite_index(self, index):
        self.image = self.image_tiles[(self.flipped_x, self.flipped_y, index)]
        self.surface = self.image.copy()
        self.rect = self.image.get_rect(center=self.rect.center)
        if self.index in ALLOWED_BG:
            self.mask = pg.mask.from_surface(self.image)
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
        new_image = pg.transform.rotate(self.surface, angle % 360)
        new_rect = new_image.get_rect(center=self.rect.center)
        self.image = new_image
        self.rect = new_rect
        if self.index in ALLOWED_BG:
            self.mask = pg.mask.from_surface(self.image)
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

    def __init__(self, path=None, state=SpriteState.unknown, waiting=False, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.path = path
        self.waiting = waiting

    def update(self):
        try:
            self.animate()
            if self.path is not None:
                self.state = SpriteState.moving
                if not self.waiting:
                    position, angle = next(self.path)
                    self.move(position)
                    self.rotate(angle + next(self.angle))
            self.play()
            self.waiting = False
        except StopIteration:
            if not self.waiting:
                self.state = SpriteState.stopped


class Text(DirectedSprite):
    """
    Subclass of `DirectedSprite` that allows for rendering text in
    addition to basic directed movement.

    Can optionally store an `action` that represents an action to be
    taken if the item is invoked somehow.
    """

    def __init__(self, text, color, size, action=None, path=None, **kwargs):
        self.color = color
        self.size = size
        self.font = pg.font.Font(FONT_NAME, size)
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
        self.image = self.font.render(self.text, True, self.color)
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


class Enemy(DirectedSprite):
    """
    Subclass of `DirectedSprite` that additionally adds subtle
    rotation to the Enemy to mimic human gait.
    """

    _layer = Layer.enemy

    def __init__(
        self,
        health: int = 100,
        cooldown=100,
        cooldown_remaining=0,
        aggro_distance=500,
        speed=2,
        collision_damage=10,
        currently_pathfinding=False,
        **kwargs
    ):
        # Tracks the offset, if any, if the image is flipped
        self.sprite_offset = Vector(0, 0)
        self.health = health
        self.cooldown = cooldown
        self.cooldown_remaining = cooldown_remaining
        self.aggro_distance = aggro_distance
        self.speed = speed
        self.collision_damage = collision_damage
        self.currently_pathfinding = currently_pathfinding
        super().__init__(**kwargs)

    def update(self):
        super().update()
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
        if self.rect.center == self._final_position:
            self.animation_state = AnimationState.stopped
            self.currently_pathfinding = False
        if self.health <= 0:
            self.animation_state = AnimationState.dying

    def direct_movement(self, target):
        self._final_position = target.rect.center
        _v1 = Vector(target.rect.center)
        _v2 = Vector(self.rect.center)
        distance = int(round(math.sqrt((_v1[0]-_v2[0])**2 + (_v1[1]-_v2[1])**2)))
        vh = (_v1 - _v2).normalize() * self.speed
        self.path = zip(
            accumulate(repeat(vh, int(distance/2)), func=operator.add, initial=_v2),
            repeat(0, int(distance/2)),
        )


class Player(Sprite):

    _layer = Layer.player

    def __init__(
        self,
        cooldown=20,
        health=100,
        damage=25,
        cooldown_remaining=0,
        position=[800, 500],
        speed=4,
        state=SpriteState.unknown,
        invulnerable_remaining=0,
        invulnerable_cooldown=20,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.state = state
        self.health = health
        self.damage = damage
        self.cooldown = cooldown
        self.position = position
        self.speed = speed
        self.cooldown_remaining = cooldown_remaining
        self.invulnerable_remaining = invulnerable_remaining
        self.invulnerable_cooldown = invulnerable_cooldown

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


class Trap(Sprite):
    _layer = Layer.trap

    def update(self):
        pass


class Shrub(Sprite):
    _layer = Layer.shrub

    def update(self):
        pass


@dataclass
class SpriteManager:

    layers: pg.sprite.LayeredUpdates
    sprites: pg.sprite.LayeredUpdates
    indices: Optional[Generator[int, None, None]]
    _last_index: Optional[int] = field(init=False, default=None)
    _last_orientation: int = field(init=False, default=0)

    def create_background(self, position, orientation=None, index=None):
        if index is None:
            index = self._last_index
        if orientation is None:
            orientation = self._last_orientation
        self.indices = cycle(ALLOWED_BG)
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
        debris = Shrub.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=index,
            orientatio=orientation
        )
        return debris

    def create_player(self, position, orientation=None, index=None):
        player = Player.create_from_sprite(
            index="edwardo",
            groups=[self.layers],
            state=SpriteState.moving,
        )
        player.move(position)
        return player

    def create_enemy(self, position, orientation=None, index=None):
        if index is None:
            index = self._last_index
        if orientation is None:
            orientation = self._last_orientation
        self.indices = cycle(ALLOWED_ENEMY)
        enemy = Enemy.create_from_sprite(
            index=next(self.indices) if index is None else index,
            groups=[self.layers],
            state=SpriteState.moving,
            sounds=None,
            frames=create_animation_roll(
                {
                    AnimationState.dying: extend(
                        ANIMATIONS["skeleton_death"], 7
                    ),
                    AnimationState.walking: cycle(extend(
                        ANIMATIONS["skeleton_walk"], 7
                    )),
                    AnimationState.stopped: cycle(extend(
                        ANIMATIONS["skeleton_stopped"], 20
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
        shrub = Shrub.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=index,
            orientation=orientation,
        )
        return shrub

    def create_projectile(self, source, target, speed=5, max_distance=900, damage=5):
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
            # It's a rock, so let's make it rotate a bit as it flies
            count(random.randint(0, 180)),
        )
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
            if sprite.layer == Layer.background:
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
            if sprite.layer in (Layer.background, Layer.shrub):
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
