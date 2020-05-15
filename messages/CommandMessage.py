from .AbstractMessage import AbstractMessage
from utils.constants import *


class CommandMessage(AbstractMessage):

    def __init__(self, client: str = '', type: str = '', timestamp: int = -1, payload: bytes = b'', sequence_number: int = -1):
        super().__init__(COMMAND_MESSAGE_ID, client, type, timestamp, payload)
        self.sequence_number = sequence_number
