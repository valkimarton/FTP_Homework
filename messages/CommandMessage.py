from Crypto.Cipher import AES
from .AbstractMessage import AbstractMessage
from utils.constants import *


class CommandMessage(AbstractMessage):

    def __init__(self, client: str = '', type: str = '', timestamp: int = -1, payload: bytes = b'',
                 sequence_number: int = -1):
        super().__init__(COMMAND_MESSAGE_ID, client, type, timestamp, payload)
        self.sequence_number = sequence_number

    def from_bytes(self, bytestring):
        self.id = self.get_valid_id_or_throw(bytestring)
        self.client = self.get_valid_client_or_throw(bytestring)
        self.type = self.get_valid_type_or_throw(bytestring, self.id)
        self.len = self.get_len(bytestring)
        self.timestamp = self.get_valid_timestamp_or_throw(bytestring)
        self.payload = self.get_payload(bytestring)
        self.sequence_number = self.get_sequence_num(bytestring)

    def header_to_bytes(self) -> bytes:
        return super().header_to_bytes() + self.sequence_number_to_bytes()

    def sequence_number_to_bytes(self):
        return self.sequence_number.to_bytes(length=4, byteorder='big')  # 4 byte-on van ábrázolva

    def get_sequence_num(self, bytestring: bytes) -> int:
        return int.from_bytes(bytestring[16:20], byteorder='big')

    def get_payload(self, bytestring: bytes) -> str:
        payload = bytestring[20:].decode('utf-8')
        return payload
