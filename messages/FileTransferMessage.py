from .AbstractMessage import AbstractMessage
from utils.constants import *


class FileTransferMessage(AbstractMessage):

    def __init__(self, client: str = '', type: str = '', timestamp: int = -1, payload: str = '', sequence_number: int = -1, last: bool = False):
        super().__init__(FILE_TRANSFER_MESSAGE_ID, client, type, timestamp, payload)
        self.sequence_number = sequence_number
        self.last = last
