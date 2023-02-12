import enum

class AnimationState(enum.Enum):
    """
    Possible animation states
    """
    stopped = "stopped"
    walking = "walking"
    dying = "dying"
    exploding = "exploding"
    firing = "firing"

    @classmethod
    def state_kills_sprite(cls, state):
        """
        Returns true when in a state that should kill sprite upon completion
        """
        return state in (cls.exploding, cls.dying)

    @classmethod
    def state_ends(cls, state):
        """
        Returns true when in a state that should end and return to stopped
        """
        return state == cls.firing


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
    """
    Possible layers which controls sprite display order
    """

    background = 0
    wall = 5
    door = 10
    shrub = 15
    debris = 20
    enemy = 25
    trap = 30
    item = 35
    buff = 40
    player = 45
    weapon = 50
    health = 55
    projectile = 60
    text = 65