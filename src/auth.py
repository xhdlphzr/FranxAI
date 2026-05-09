# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Authentication - ECC key management, JWT tokens, bcrypt, login_required decorator
"""

import os
import base64
import secrets
from functools import wraps
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from flask import request, jsonify

from src.state import load_config, save_config

PRIVATE_KEY_FILE = "private.key"
PUBLIC_KEY_FILE = "public.key"

# ECC curve: NIST P-256
CURVE = ec.SECP256R1()

# HKDF info string for domain separation
HKDF_INFO = b'franxagent-ecc-encryption'

def generate_ecc_keys():
    private_key = ec.generate_private_key(CURVE)
    public_key = private_key.public_key()
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    if os.name != 'nt':
        os.chmod(PRIVATE_KEY_FILE, 0o600)
    print("✅ Generated ECC key pair (P-256).")

def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key_pem():
    with open(PUBLIC_KEY_FILE, "r") as f:
        return f.read()

def ecc_decrypt(private_key, encrypted_data: dict) -> bytes:
    """
    Decrypt data encrypted with ECIES (ECDH + HKDF + AES-256-GCM).

    encrypted_data expects:
        - ephemeral_key: base64-encoded SPKI DER of the ephemeral public key
        - iv: base64-encoded 12-byte nonce
        - ciphertext: base64-encoded AES-GCM ciphertext (includes 16-byte tag)
    """
    ephemeral_key_der = base64.b64decode(encrypted_data['ephemeral_key'])
    iv = base64.b64decode(encrypted_data['iv'])
    ciphertext = base64.b64decode(encrypted_data['ciphertext'])

    # Import client's ephemeral public key
    ephemeral_public_key = serialization.load_der_public_key(ephemeral_key_der)

    # ECDH key exchange
    shared_secret = private_key.exchange(ec.ECDH(), ephemeral_public_key)

    # Derive AES-256 key via HKDF
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=HKDF_INFO,
    ).derive(shared_secret)

    # Decrypt with AES-256-GCM (tag is already appended to ciphertext)
    aesgcm = AESGCM(derived_key)
    return aesgcm.decrypt(iv, ciphertext, None)

def generate_jwt_token():
    config = load_config()
    secret = config.get("jwt_secret")
    if not secret:
        secret = secrets.token_urlsafe(32)
        config["jwt_secret"] = secret
        save_config(config)
    now = datetime.now(timezone.utc)
    payload = {
        "exp": now + timedelta(hours=1),
        "iat": now,
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_jwt_token(token):
    config = load_config()
    secret = config.get("jwt_secret")
    if not secret:
        return False
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except jwt.InvalidTokenError:
        return False

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        config = load_config()
        if "password_hash" not in config:
            return f(*args, **kwargs)
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or not verify_jwt_token(token):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# Initialize ECC keys on first run (or migrate from old RSA keys)
if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
    generate_ecc_keys()
else:
    # Check if existing key is RSA (from old version) and regenerate as ECC
    try:
        key = load_private_key()
        if not isinstance(key, ec.EllipticCurvePrivateKey):
            print("⚠️ Existing key is not ECC, regenerating...")
            os.remove(PRIVATE_KEY_FILE)
            os.remove(PUBLIC_KEY_FILE)
            generate_ecc_keys()
    except Exception:
        print("⚠️ Failed to load existing key, regenerating...")
        generate_ecc_keys()