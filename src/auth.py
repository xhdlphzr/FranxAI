# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Authentication - RSA key management, JWT tokens, bcrypt, login_required decorator
"""

import os
import secrets
from functools import wraps
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from flask import request, jsonify

from src.state import load_config, save_config

PRIVATE_KEY_FILE = "private.key"
PUBLIC_KEY_FILE = "public.key"


def generate_rsa_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
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
    print("✅ Generated RSA key pair.")


def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key_pem():
    with open(PUBLIC_KEY_FILE, "r") as f:
        return f.read()


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


# Initialize RSA keys on first run
if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
    generate_rsa_keys()