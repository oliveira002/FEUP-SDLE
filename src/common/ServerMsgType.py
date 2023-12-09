from enum import Enum


class ServerMsgType(str, Enum):
    CONNECT = "CONNECT"
    REPLY = "REPLY"
    HEARTBEAT = "HEARTBEAT"
    REPLICATE = "REPLICATE"
    ACK = "ACK"
    REBALANCE = "REBALANCE"
    HANDOFF = "HANDOFF"
    HANDOFF_RECV = "HANDOFF_RECV"
