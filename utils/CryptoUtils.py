from Crypto.Cipher import Salsa20
from Crypto.Hash import SHA256
from Crypto.Hash import SHAKE128


def string_to_32_byte_key(str: str) -> bytes:
    shake = SHAKE128.new()
    shake.update(str.encode('utf-8'))
    return shake.read(32)


def get_password_hash(password: str) -> bytes:
    password_bytestring = password.encode('utf-8')
    hash_object = SHA256.new(data=password_bytestring)
    return hash_object.digest()


def get_shared_secret_by_password(password: str) -> bytes:
    encrypted_shared_secret_with_nonce = b'\x81C\xde\x00\t~\xd8a\xe52\xd8y\xae\x1d\x04\x9bV\xa6\x86\x81%m\xc4'  # b'123456789123456', password: 'password'
    # TODO: read encrypted session key from database

    decrypt_key = string_to_32_byte_key(password)
    nonce = encrypted_shared_secret_with_nonce[:8]
    encrypted_shared_secret = encrypted_shared_secret_with_nonce[8:]
    cipher = Salsa20.new(key=decrypt_key, nonce=nonce)
    shared_secret = cipher.decrypt(encrypted_shared_secret)

    return shared_secret


'''

# checking password hash
print(get_password_hash('password'))

# encrypting a shared secret
shared_secret = b'shared_secret_A_0123456789012345'
password = 'password'
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
