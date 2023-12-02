from enum import Enum


class ServerMessageType(Enum):
    CONNECT = 1
    REPLY = 2
    HEARTBEAT = 3
