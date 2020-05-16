from .AbstractMessage import AbstractMessage
from utils.constants import *


class CommandMessage(AbstractMessage):

    def __init__(self, client: str = '', type: str = '', timestamp: int = -1, payload: bytes = b'', sequence_number: int = -1):
        super().__init__(COMMAND_MESSAGE_ID, client, type, timestamp, payload)
        self.sequence_number = sequence_number

    def from_bytes(self, bytestring):
        print('Not implemented')

    def header_to_bytes(self) -> bytes:
        return super().header_to_bytes() + self.sequence_number_to_bytes()

    def sequence_number_to_bytes(self):
        return self.sequence_number.to_bytes(length=4, byteorder='big')     # 4 byte-on van ábrázolva