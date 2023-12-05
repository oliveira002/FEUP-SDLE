from enum import Enum


class ServerMsgType(Enum):
    CONNECT = "CONNECT"
    REPLY = "REPLY"
    HEARTBEAT = "HEARTBEAT"
    REPLICATE = "REPLICATE"
