from enum import Enum, auto

class gameStates(Enum):
    WAIT_FOR_MAGNETO = auto()
    WAIT_FOR_VALVE = auto()
    WAIT_FOR_OIL_PUMP = auto()
    WAIT_FOR_STARTER = auto()
    END = auto()