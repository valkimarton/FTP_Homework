from pprint import pprint

from netsim.netinterface import *
from utils.constants import *

# The class is not really abstract, but should not be instantiated :)

class AbstractMessage:

    def __init__(self, id: str, client: str, type: str, timestamp: int, payload: str):
        self.id = id
        self.client = client
        self.type = type
        self.len = len(payload)  # the Message object contains the plaintext message -> payload = string
        self.timestamp = timestamp
        self.payload = payload

    # change to to_bytestring
    def to_bytes(self) -> bytes:
        return self.header_to_bytes() + self.payload_to_bytes()

    def header_to_bytes(self) -> bytes:
        return self.id.encode('utf-8') + self.client.encode('utf-8') + self.type.encode('utf-8') + self.len_to_byte() + self.timestamp_to_byte()

    def payload_to_bytes(self) -> bytes:
        return self.payload.encode('utf-8')

    def from_bytes(self, bytestring):
        print('Implemented in subclasses. Tries to create a message object from the string parameter')

    '''
    def header_from_bytes
    
    def payload_from_bytes
    '''

    def get_valid_id_or_throw(self, bytestring: bytes) -> str:
        id = bytestring[0:1].decode('utf-8')
        if id not in ID_SPACE:
            raise Exception('Invalid message ID')
        return id

    def get_valid_client_or_throw(self, bytestring: bytes) -> str:
        client = bytestring[1:2].decode('utf-8')
        if client not in CLIENT_SPACE:
            raise Exception('Invalid Client identifier')
        return client

    def get_valid_type_or_throw(self, bytestring: bytes, message_id: str) -> str:
        type = bytestring[2:5].decode('utf-8')
        if type not in TYPE_SPACE[message_id]:
            raise Exception('Invalid type field for message id: ' + message_id)
        return type

    def get_len(self, bytestring: bytes) -> int:
        return int.from_bytes(bytestring[5:6], byteorder='big')

    def get_valid_timestamp_or_throw(self, bytestring: bytes) -> int:
        timestamp = int.from_bytes(bytestring[6:16], byteorder='big')

        # validation logic here?

        return timestamp

    def get_payload(self, bytestring: bytes) -> str:
        print('Should be implemented in subclasses')

    def len_to_byte(self) -> bytes:
        if self.len > 255:
            raise Exception('message len is bigger than 255 bytes. encoding failed')
        return self.len.to_bytes(length=1, byteorder='big')

    def timestamp_to_byte(self) -> bytes:
        # valiation logic here? (timestamp must be small than 2^80 -1 .... ha csak ez,a kkor azzan ne foglalkozzunk most)
        return self.timestamp.to_bytes(length=10, byteorder='big')

    def print(self):
        pprint(self.__dict__)

