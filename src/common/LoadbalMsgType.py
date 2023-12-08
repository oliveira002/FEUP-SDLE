from enum import Enum


class LoadbalMsgType(str, Enum):
    HEARTBEAT = "HEARTBEAT"
    JOIN_RING = "JOIN_RING"
    RING = "RING"
    SV_OFFLINE = "SV_OFFLINE"