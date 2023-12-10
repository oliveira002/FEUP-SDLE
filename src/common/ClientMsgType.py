import os
import sys
from enum import Enum

# Define module
current_path = os.path.dirname(__file__) + '/../..'
sys.path.append(current_path)


class ClientMsgType(str, Enum):
    POST = "POST"
    GET = "GET"
