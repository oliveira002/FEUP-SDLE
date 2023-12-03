from enum import Enum


class ServerMessageType(Enum):
    CONNECT = "CONNECT"
    REPLY = "REPLY"
    HEARTBEAT = "HEARTBEAT"
