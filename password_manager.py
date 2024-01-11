#!/usr/bin/env python3

import os
from cryptography.fernet import Fernet


class PasswordManager:
    def __init__(self, key_filename='key.key'):
        self.key = None
        self.key_filename = key_filename
        self.load_key()

    def generate_key(self):
        key = Fernet.generate_key()
        with open(self.key_filename, 'wb') as key_file:
            key_file.write(key)

    def load_key(self):
        if not os.path.exists(self.key_filename):
            self.generate_key()
        with open(self.key_filename, 'rb') as key_file:
            self.key = key_file.read()

    def encrypt_password(self, password):
        fernet = Fernet(self.key)
        return fernet.encrypt(password.encode())

    def decrypt_password(self, encrypted_password):
        fernet = Fernet(self.key)
        return fernet.decrypt(encrypted_password).decode()

    def store_password(self, username, password):
        encrypted_password = self.encrypt_password(password)
        with open(f'{username}.pwd', 'wb') as pwd_file:
            pwd_file.write(encrypted_password)

    def retrieve_password(self, username):
        try:
            with open(f'{username}.pwd', 'rb') as pwd_file:
                encrypted_password = pwd_file.read()
                return self.decrypt_password(encrypted_password)
        except FileNotFoundError:
            return None

    def cleanup(self, username):
        pwd_file = f'{username}.pwd'
        if os.path.exists(self.key_filename):
            os.remove(self.key_filename)
        else:
            print("Error in deleting key.file - file doesnt exist")

        if os.path.exists(pwd_file):
            os.remove(pwd_file)
        else:
            print(f'Error in deleting {username}.pwd - file doesnt exist')

def load_encryption_key(key_filename):
    with open(key_filename, "rb") as key_file:
        return key_file.read()

def load_encrypted_password(password_filename):
    with open(password_filename, "rb") as password_file:
        return password_file.read()

def decrypt_password(encrypted_password, key):
    f = Fernet(key)
    decrypted_password = f.decrypt(encrypted_password).decode()
    return decrypted_password