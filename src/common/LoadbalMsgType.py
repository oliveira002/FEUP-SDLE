from enum import Enum


class LoadbalMsgType(str, Enum):
    HEARTBEAT = "HEARTBEAT"
