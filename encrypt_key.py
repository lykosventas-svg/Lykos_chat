"""Utility script to encrypt the MaaS API key for storage in config.json.

Usage:
    python encrypt_key.py

The script will:
1. Prompt for the API key (or read from .env)
2. Prompt for a password (CONFIG_SECRET)
3. Output the encrypted value to paste into config.json

The encrypted value should be prefixed with "enc:" in config.json:
    "api_key": "enc:gAAAAABm..."
"""

import base64
import hashlib
import secrets
import getpass
import os

from dotenv import load_dotenv
load_dotenv()

_SALT = b"lykos_salt_2026"


def _derive_fernet_key(password: str) -> bytes:
    raw = hashlib.pbkdf2_hmac("sha256", password.encode(), _SALT, 100_000)
    return base64.urlsafe_b64encode(raw)


def encrypt_value(value: str, password: str) -> str:
    from cryptography.fernet import Fernet
    key = _derive_fernet_key(password)
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()


def main():
    print("=== Encriptador de API Key para config.json ===\n")

    # Try to read from .env first
    env_key = os.getenv("MAAS_API_KEY", "").strip()
    if env_key:
        use_env = input(f"Se encontro MAAS_API_KEY en .env. Usar? [S/n]: ").strip().lower()
        if use_env != "n":
            api_key = env_key
        else:
            api_key = getpass.getpass("Ingrese el API key: ")
    else:
        api_key = getpass.getpass("Ingrese el API key: ")

    print("\nAhora ingrese la contraseña de encriptacion (CONFIG_SECRET).")
    print("Esta contraseña debe configurarse como variable de entorno en Dokploy.")
    password = getpass.getpass("Contraseña: ")

    if not password:
        print("Error: la contraseña no puede estar vacia.")
        return

    encrypted = encrypt_value(api_key, password)
    print(f"\n=== Resultado ===")
    print(f'Pegue esto en config.json:')
    print(f'"api_key": "enc:{encrypted}"')
    print(f'\nConfigure en Dokploy:')
    print(f'CONFIG_SECRET={password}')


if __name__ == "__main__":
    main()
