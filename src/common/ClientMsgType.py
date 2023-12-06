from enum import Enum


class ClientMsgType(str, Enum):
    POST = "POST"
    GET = "GET"
