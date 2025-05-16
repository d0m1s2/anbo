from enum import Enum, auto

class gameStates(Enum):
    GAME_BEGIN = auto()
    WAIT_FOR_MAGNETO = auto()
    WAIT_FOR_THROTTLE = auto()
    WAIT_FOR_VALVE = auto()
    WAIT_FOR_OIL_PUMP = auto()
    WAIT_FOR_STARTER = auto()
    END = auto()
    IDLE = auto()