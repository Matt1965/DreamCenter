import enum

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


class MovementType(enum.Enum):
    """
    Possible types of movement
    """
    chase = "chase"
    wander = "wander"
    wander_chase = "wander_chase"
    ranged_chase = "ranged_chase"


class Layer(enum.IntEnum):

    background = 0
    wall = 20
    door = 30
    enemy = 40
    shrub = 50
    trap = 60
    item = 65
    player = 70
    health = 80
    buff = 85
    projectile = 90
    text = 100