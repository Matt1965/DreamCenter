import enum
import pygame as pg
from pygame import Vector2 as Vector
from dataclasses import dataclass
from dreamcenter.constants import (
    IMAGE_SPRITES,
    TILE_HEIGHT,
    TILE_WIDTH,
    FONT_NAME,
    FONT_SIZE,
    SOUNDS,
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
    enemy = 20
    shrub = 25
    projectile = 30


class Sprite(pg.sprite.Sprite):
    @classmethod
    def create_from_tile(
        cls,
        index,
        groups,
        image_tiles=IMAGE_SPRITES,
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
            rect=rect,
            **kwargs,
        )

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
        sound=None,
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
        self.sound = sound
        self.image_tiles = image_tiles
        self.index = index
        self.rect = rect
        self.orientation = orientation
        self.flipped_x = flipped_x
        self.flipped_y = flipped_y
        self.frames = frames
        self._last_angle = None
        self.animation_state = animation_state
        if self.image is not None:
            self.mask = pg.mask.from_surface(self.image)
            self.surface = self.image.copy()
            self.rotate(self.orientation)
        if self.rect is not None and position is not None:
            self.move(position)

    def set_sprite_index(self, index):
        self.image = self.image_sprites[(self.flipped_x, self.flipped_y, index)]
        self.surface = self.image.copy()
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pg.mask.from_surface(self.image)
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
        self.mask = pg.mask.from_surface(self.image)
        self._last_angle = angle

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
            self.animation_state = AnimationState.stopped

    def play(self):
        if self.sound is not None and pg.mixer and self.channel is not None:
            effect_name = next(self.sound)
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

    def __init__(self, path, state=SpriteState.unknown, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.path = path

    def update(self):
        try:
            self.animate()
            if self.path is not None:
                self.state = SpriteState.moving
                position, angle = next(self.path)
                self.move(position)
                self.rotate(angle + next(self.angle))
            self.play()
        except StopIteration:
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


class Enemy(DirectedSprite):
    """
    Subclass of `DirectedSprite` that additionally adds subtle
    rotation to the Enemy to mimic human gait.
    """

    _layer = Layer.enemy

    def __init__(self, health: int = 100, **kwargs):
        # Tracks the offset, if any, if the image is flipped
        self.sprite_offset = Vector(0, 0)
        self.health = health
        super().__init__(**kwargs)

    def update(self):
        try:
            self.animate()
            if self.path is None:
                return
            if self.animation_state == AnimationState.dying:
                self.play()
                return
            self.state = SpriteState.moving
            position, _, flipx = next(self.path)
            # The state of flipx has changed since we were last
            # invoked; that happens whenever our orientation is
            # supposed to change.
            if flipx != self.flipped_x:
                # Acknowledge flipx is changed and update the internal state.
                self.flipped_x = flipx
                # Calculate the centroid of our CURRENT mask,
                # before we ask `set_sprite_index` to flip our
                # image.
                centroid = self.mask.centroid()
                # Change to our current index (but actually flip
                # it because we set flipped_x before)
                self.set_sprite_index(self.index)
                # Now get the _new_ centroid
                new_centroid = self.mask.centroid()
                # The delta between both centroids is the offset
                # we must apply to our movement to ensure the
                # flipped image is placed in the exact same
                # position as before
                self.sprite_offset = Vector(new_centroid) - Vector(centroid)
            if flipx:
                self.move(position - self.sprite_offset)
            else:
                self.move(position)
            self.play()
        except StopIteration:
            self.state = SpriteState.stopped


class Background(Sprite):
    _layer = Layer.background

    def update(self):
        pass

class Shrub(Sprite):
    _layer = Layer.shrub

    def update(self):
        pass

@dataclass
class SpriteManager:

    layers: pg.sprite.LayeredUpdates
    selected: pg.sprite.LayeredUpdates
    level: list
    sprites: pg.sprite.LayeredUpdates

    def create(cls, layers, level):
        return cls(layers=layers, level=level, selected=pg.sprite.LayeredUpdates())

    def empty(self):
        self.sprites.empty()

    def create_background(self, position, orientation=None, index=None):
        background = Background.create_from_tile(
            sounds=None,
            groups=[self.layers],
            index=index,
            orientatio=orientation
        )
        return background

    def create_debris(self, position, orientation=None, index=None):
        debris = Debris.create_from_sprite(
            sounds=None,
            groups=[self.layers],
            index=index,
            orientatio=orientation
        )
        return debris

    def select_sprites(self, sprites, position=None):
        self.selected.add(sprites)
        if position is not None:
            self.move(position)

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
