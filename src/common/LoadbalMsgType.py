import os
import sys
from enum import Enum

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)

class LoadbalMsgType(str, Enum):
    HEARTBEAT = "HEARTBEAT"
    JOIN_RING = "JOIN_RING"
    RING = "RING"
    SV_OFFLINE = "SV_OFFLINE"
