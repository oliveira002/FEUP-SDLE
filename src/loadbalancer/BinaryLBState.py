import os
import sys
from enum import Enum

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)


class BinaryLBState(str, Enum):
    NONE = "NONE"

    SELF_PRIMARY = "PRIMARY"
    SELF_BACKUP = "BACKUP"
    SELF_ACTIVE = "ACTIVE"
    SELF_PASSIVE = "PASSIVE"

    PEER_PRIMARY = "PRIMARY"
    PEER_BACKUP = "BACKUP"
    PEER_ACTIVE = "ACTIVE"
    PEER_PASSIVE = "PASSIVE"
    CLIENT_REQUEST = "CLIENT_REQUEST"


lbfsm_state_map = {
    BinaryLBState.SELF_PRIMARY: {
        BinaryLBState.PEER_BACKUP: ("Connected to backup (passive), ready as active", BinaryLBState.SELF_ACTIVE),
        BinaryLBState.PEER_ACTIVE: ("Connected to backup (active), ready as passive", BinaryLBState.SELF_PASSIVE)
    },
    BinaryLBState.SELF_BACKUP: {
        BinaryLBState.PEER_ACTIVE: ("Connected to primary (active), ready as passive", BinaryLBState.SELF_PASSIVE),
        BinaryLBState.CLIENT_REQUEST: ("", False)
    },
    BinaryLBState.SELF_ACTIVE: {
        BinaryLBState.PEER_ACTIVE: ("Fatal error - dual actives, aborting", False)
    },
    BinaryLBState.SELF_PASSIVE: {
        BinaryLBState.PEER_PRIMARY: ("Primary (passive) is restarting, ready as active", BinaryLBState.SELF_ACTIVE),
        BinaryLBState.PEER_BACKUP: ("Backup (passive) is restarting, ready as active", BinaryLBState.SELF_ACTIVE),
        BinaryLBState.PEER_PASSIVE: ("Fatal error - dual passives, aborting", False),
        BinaryLBState.CLIENT_REQUEST: (BinaryLBState.CLIENT_REQUEST, True)  # Say true, check peer later
    }
}


class LoadbalancerState(object):
    def __init__(self, state, event, peer_expiry):
        self.state = state
        self.event = event
        self.peer_expiry = peer_expiry


class BStarException(Exception):
    pass
