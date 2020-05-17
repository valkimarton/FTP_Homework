from pprint import pprint
import time

from netsim.netinterface import *
from utils.constants import *
from utils.GeneralUtils import *

# The class is not really abstract, but should not be instantiated :)
class AbstractMessage:

    # Konstruktor
    def __init__(self, id: str, client: str, type: str, timestamp: int, payload: bytes):
        self.id = id
        self.client = client
        self.type = type
        self.len = int(len(payload) / 16) # the Message object contains the unencrypted message in bytes -> payload = bytes
        self.timestamp = timestamp
        if isinstance(payload, bytes):
            self.payload: bytes = payload
        else:
            raise Exception('payload type must be: bytes')

    # Visszaadja a Message objektum bytestring reprezentációját
    def to_bytes(self) -> bytes:
        return self.header_to_bytes() + self.payload

    def header_to_bytes(self) -> bytes:
        return self.id.encode('utf-8') + self.client.encode('utf-8') + self.type.encode('utf-8') + self.len_to_byte() + self.timestamp_to_byte()

    # bytes üzenetreprezentációból beolvassa a mezőket
    # A leszármazottakban egyszerűbb egyesével implementálni szerintem
    def from_bytes(self, bytestring):
        print('Implemented in subclasses. Tries to create a message object from the string parameter')

    # getting ID from bytestring + validation
    def get_valid_id_or_throw(self, bytestring: bytes) -> str:
        id = bytestring[0:1].decode('utf-8')
        if id not in ID_SPACE:
            raise Exception('Invalid message ID: ' + id)
        return id

    # getting CLIENT from bytestring + validation
    def get_valid_client_or_throw(self, bytestring: bytes) -> str:
        client = bytestring[1:4].decode('utf-8')
        if client not in CLIENT_SPACE:
            raise Exception('Invalid Client identifier: ' + client)
        return client

    # getting TYPE from bytestring + validation
    def get_valid_type_or_throw(self, bytestring: bytes, message_id: str) -> str:
        type = bytestring[4:7].decode('utf-8')
        if type not in TYPE_SPACE[message_id]:
            raise Exception('Invalid type field: ' + type + 'for message id: ' + message_id)
        return type

    # getting LEN from bytestring
    def get_len(self, bytestring: bytes) -> int:
        return int.from_bytes(bytestring[7:8], byteorder='big')

    # getting TIMESTAMP from bytestring + validation
    def get_valid_timestamp_or_throw(self, bytestring: bytes) -> int:
        timestamp = int.from_bytes(bytestring[8:16], byteorder='big')
        if timestamp > get_current_timestamp():
            raise Exception('message timestamp is bigger than current time')
        # if timestamp < get_random_session_key() - 30:         TODO
        #     raise Exception('message timestamp is too old')
        return timestamp

    # getting DATA/PAYLOAD from bytestring
    def get_payload(self, bytestring: bytes) -> bytes:
        print('Should be implemented in subclasses')

    # convert LEN to bytestring
    def len_to_byte(self) -> bytes:
        if self.len > 255:
            raise Exception('message len is bigger than 255 bytes. encoding failed')
        return self.len.to_bytes(length=1, byteorder='big')

    # convert TIMESTAMP to bytestring
    def timestamp_to_byte(self) -> bytes:
        # valiation logic here? (timestamp must be small than 2^80 -1 .... ha csak ez,a kkor azzan ne foglalkozzunk most)
        return self.timestamp.to_bytes(length=10, byteorder='big')

    # print Message structure
    def print(self):
        pprint(self.__dict__)

