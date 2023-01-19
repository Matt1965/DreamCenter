import enum


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
    game_over = "game_ended"
    # Game is exiting
    quitting = "quitting"


class StateError(Exception):
    """
    Raised if the game is in an unexpected game state at a point
    where we expect it to be in a different state.
    """