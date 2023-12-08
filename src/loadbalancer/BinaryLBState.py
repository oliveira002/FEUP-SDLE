from time import time
from enum import IntEnum


class BinaryLBState(IntEnum):
    NONE = 0

    SELF_PRIMARY = 1
    SELF_BACKUP = 2
    SELF_ACTIVE = 3
    SELF_PASSIVE = 4

    PEER_PRIMARY = 1
    PEER_BACKUP = 2
    PEER_ACTIVE = 3
    PEER_PASSIVE = 4
    CLIENT_REQUEST = 5


lbfsm_state_map = {
    BinaryLBState.SELF_PRIMARY: {
        BinaryLBState.PEER_BACKUP: ("Connected to backup, ready as active", BinaryLBState.SELF_ACTIVE),
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
