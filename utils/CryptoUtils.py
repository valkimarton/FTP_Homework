from Crypto.Cipher import Salsa20
from Crypto.Hash import SHA256
from Crypto.Hash import SHAKE128
from Crypto.Cipher import AES
from server_root.database import database
from messages import AbstractMessage, HandshakeMessage, CommandMessage, FileTransferMessage
from utils.constants import *

# creating 32 byte key from password. Used for shared_secret encryption
def string_to_32_byte_key(str: str) -> bytes:
    shake = SHAKE128.new()
    shake.update(str.encode('utf-8'))
    return shake.read(32)

# SHA256 password hash. Used to validate password
def get_password_hash(password: str) -> bytes:
    password_bytestring = password.encode('utf-8')
    hash_object = SHA256.new(data=password_bytestring)
    return hash_object.digest()

# decrypt encrypted shared_secret in database with the help of a valid password
def get_shared_secret_by_client(client: str, secret_encryption_key: str) -> bytes:
    encrypted_shared_secret_with_nonce = database[client]['encrypted_shared_secret']

    decrypt_key = string_to_32_byte_key(secret_encryption_key)
    nonce = encrypted_shared_secret_with_nonce[:8]
    encrypted_shared_secret = encrypted_shared_secret_with_nonce[8:]
    cipher = Salsa20.new(key=decrypt_key, nonce=nonce)
    shared_secret = cipher.decrypt(encrypted_shared_secret)

    return shared_secret

# encrypt and authenticate message with AES GCM
def encrypt_message(message: AbstractMessage, key: bytes) -> bytes:
    message_in_bytes = message.to_bytes()
    public_part = message_in_bytes[0:4]        # ID and CLIEND fields are not encrypted, becouse they have to be read before decryption
    secret_part = message_in_bytes[4:]

    # Encryption
    cipher = AES.new(key, AES.MODE_GCM)     # default MAC length: 16 byte. Default nonce: random 16 byte
    cipher.update(public_part)
    ciphertext, auth_tag = cipher.encrypt_and_digest(secret_part)
    nonce = cipher.nonce

    return public_part + ciphertext + auth_tag + nonce

def decrypt_message(encrypted_message: bytes, key: bytes) -> AbstractMessage:

    public_part = encrypted_message[0:4]
    encrypted_secret_part = encrypted_message[4:-32]
    auth_tag = encrypted_message[-32:-16]
    nonce = encrypted_message[-16:]

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    cipher.update(public_part)
    decrypted_secret_part = cipher.decrypt_and_verify(encrypted_secret_part, auth_tag)

    decrypted_message = public_part + decrypted_secret_part
    id = decrypted_message[0:1].decode('utf-8')

    if id == HANDSHAKE_MESSAGE_ID:
        message = HandshakeMessage.HandshakeMessage()
        message.from_bytes(decrypted_message)
        return message
    elif id == COMMAND_MESSAGE_ID:
        message = CommandMessage.CommandMessage()
        message.from_bytes(decrypted_message)
        return message
    elif id == FILE_TRANSFER_MESSAGE_ID:
        message = FileTransferMessage.FileTransferMessage()
        message.from_bytes(decrypted_message)
        return message
    else:
        print('Invalid message ID after decryption: ', id)



'''
# Encryption test TODO: remove
msg = HandshakeMessage.HandshakeMessage('C', 'NEW', 123456789, b'test_message')
key = b'0123456789012345'
encrypted_message = encrypt_message(msg, key)
decrypted_message = decrypt_message(encrypted_message, key)
decrypted_message.print()
print(type(decrypted_message))

# checking password hash
print(get_password_hash('password'))

# checking get_shared_secret_by_password
print(get_shared_secret_by_password('C', 'password'))


# encrypting a shared secret
shared_secret = b'shared_secret_C_0123456789012345'
password = 'secret_encryption_key'
secret = string_to_32_byte_key(password)
print(len(secret))
cipher = Salsa20.new(key=secret)
msg = cipher.nonce + cipher.encrypt(shared_secret)

# dencrypting a shared secret
secret = string_to_32_byte_key(password)
msg_nonce = msg[:8]
ciphertext = msg[8:]
cipher = Salsa20.new(key=secret, nonce=msg_nonce)
shared_secret_end = cipher.decrypt(ciphertext)

print(shared_secret_end)
print(msg)
print(len(msg))

'''
