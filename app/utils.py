from django.utils.timezone import now

def time_since(timestamp):
    if not timestamp:
        return "Unknown"

    diff = now() - timestamp

    seconds = diff.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    weeks = days // 7
    months = days // 30
    years = days // 365

    if seconds < 10:
        return "A few seconds ago"
    elif seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif minutes < 2:
        return "1 min ago"
    elif minutes < 60:
        return f"{int(minutes)} mins ago"
    elif hours < 2:
        return "1 hour ago"
    elif hours < 24:
        return f"{int(hours)} hours ago"
    elif days < 2:
        return "1 day ago"
    elif days < 7:
        return f"{int(days)} days ago"
    elif weeks < 2:
        return "1 week ago"
    elif weeks < 4:
        return f"{int(weeks)} weeks ago"
    elif months < 2:
        return "1 month ago"
    elif months < 12:
        return f"{int(months)} months ago"
    elif years < 2:
        return "1 year ago"
    else:
        return f"{int(years)} years ago"

import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from django.conf import settings
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.Cipher import AES as DjangoAES
from Crypto.Util.Padding import unpad

def generate_aes_key():
    return base64.urlsafe_b64encode(get_random_bytes(32))

def aes_encrypt(data, key):
    key = base64.urlsafe_b64decode(key)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(json.dumps(data).encode(), AES.block_size))
    return {
        'iv': base64.b64encode(iv).decode(),
        'ciphertext': base64.b64encode(ct_bytes).decode()
    }

def encrypt_key_with_secret_key(aes_key):
    secret = settings.SECRET_KEY[:32].encode()
    cipher = DjangoAES.new(secret, AES.MODE_ECB)
    padded_key = pad(base64.urlsafe_b64decode(aes_key), AES.block_size)
    encrypted = cipher.encrypt(padded_key)
    return base64.b64encode(encrypted).decode()

def aes_decrypt(ciphertext, iv, key):
    key = base64.urlsafe_b64decode(key)
    iv = base64.b64decode(iv)
    ciphertext = base64.b64decode(ciphertext)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return json.loads(decrypted_data.decode())

def decrypt_key_with_secret_key(encrypted_key):
    secret = settings.SECRET_KEY[:32].encode()
    cipher = DjangoAES.new(secret, AES.MODE_ECB)
    decrypted = unpad(cipher.decrypt(base64.b64decode(encrypted_key)), AES.block_size)
    return base64.urlsafe_b64encode(decrypted).decode()
