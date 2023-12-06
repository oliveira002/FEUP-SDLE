from enum import Enum


class ServerMsgType(str, Enum):
    CONNECT = "CONNECT"
    REPLY = "REPLY"
    HEARTBEAT = "HEARTBEAT"
    REPLICATE = "REPLICATE"
    ACK = "ACK"
