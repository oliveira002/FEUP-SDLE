import os
import sys
from enum import Enum

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)


class ServerMsgType(str, Enum):
    CONNECT = "CONNECT"
    REPLY = "REPLY"
    HEARTBEAT = "HEARTBEAT"
    REPLICATE = "REPLICATE"
    ACK = "ACK"
    REBALANCE = "REBALANCE"
    HANDOFF = "HANDOFF"
    HANDOFF_RECV = "HANDOFF_RECV"
