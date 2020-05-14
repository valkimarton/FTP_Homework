from .AbstractMessage import AbstractMessage
from utils.constants import *


class HandshakeMessage(AbstractMessage):

    def __init__(self, client: str = '', type: str = '', timestamp: int = -1, payload: str = ''):
        super().__init__(HANDSHAKE_MESSAGE_ID, client, type, timestamp, payload)

    '''
    def header_to_bytes(self) -> bytes:
        return super().header_to_bytes()          # nem kell se sequence_number, se más itt

    def payload_to_bytes(self) -> bytes:
        return super().payload_to_bytes()
    '''
    def from_bytes(self, bytestring):
        self.id = self.get_valid_id_or_throw(bytestring)
        self.client = self.get_valid_client_or_throw(bytestring)
        self.type = self.get_valid_type_or_throw(bytestring, self.id)
        self.len = self.get_len(bytestring)
        self.timestamp = self.get_valid_timestamp_or_throw(bytestring)
        self.payload = self.get_payload(bytestring)

    def get_payload(self, bytestring: bytes) -> str:
        return bytestring[16:].decode('utf-8')

    # ....