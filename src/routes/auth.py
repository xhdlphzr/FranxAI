# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Auth Routes - /api/public-key, /api/setup, /api/login, /api/check-auth, /api/i18n
"""

import base64
import yaml
from pathlib import Path
import bcrypt
from flask import Blueprint, request, jsonify
from src.auth import load_private_key, load_public_key_pem, generate_jwt_token, verify_jwt_token
from src.state import load_config, save_config

auth_bp = Blueprint('auth', __name__)

I18N_DIR = Path(__file__).parent.parent.parent / "i18n"


@auth_bp.route('/api/public-key', methods=['GET'])
def get_public_key():
    return jsonify({'public_key': load_public_key_pem()})


@auth_bp.route('/api/setup', methods=['POST'])
def setup_password():
    config = load_config()
    if "password_hash" in config:
        return jsonify({'error': 'Password already set'}), 400
    data = request.get_json()
    encrypted_password = data.get('password')
    if not encrypted_password:
        return jsonify({'error': 'Missing password'}), 400
    private_key = load_private_key()
    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        decrypted = private_key.decrypt(
            base64.b64decode(encrypted_password),
            padding.PKCS1v15()
        )
        password = decrypted.decode()
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {e}'}), 400
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    config["password_hash"] = hashed.decode()
    import secrets
    if "jwt_secret" not in config:
        config["jwt_secret"] = secrets.token_urlsafe(32)
    save_config(config)
    token = generate_jwt_token()
    return jsonify({'status': 'success', 'token': token})


@auth_bp.route('/api/login', methods=['POST'])
def login():
    config = load_config()
    if "password_hash" not in config:
        return jsonify({'error': 'Password not set'}), 400
    data = request.get_json()
    encrypted_password = data.get('password')
    if not encrypted_password:
        return jsonify({'error': 'Missing password'}), 400
    private_key = load_private_key()
    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        decrypted = private_key.decrypt(
            base64.b64decode(encrypted_password),
            padding.PKCS1v15()
        )
        password = decrypted.decode()
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {e}'}), 400
    stored_hash = config["password_hash"].encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        token = generate_jwt_token()
        return jsonify({'status': 'success', 'token': token})
    else:
        return jsonify({'error': 'Invalid password'}), 401


@auth_bp.route('/api/check-auth', methods=['GET'])
def check_auth():
    config = load_config()
    password_set = "password_hash" in config
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    valid = False
    if token and password_set:
        valid = verify_jwt_token(token)
    return jsonify({'password_set': password_set, 'authenticated': valid})


@auth_bp.route('/api/i18n', methods=['GET'])
def get_i18n():
    try:
        config = load_config()
        lang = config.get("language", "en")
    except Exception:
        lang = "en"
    lang_file = I18N_DIR / f"{lang}.yaml"
    if not lang_file.exists():
        lang_file = I18N_DIR / "en.yaml"
    if not lang_file.exists():
        return jsonify({'language': 'en', 'translations': {}})
    with open(lang_file, 'r', encoding='utf-8') as f:
        translations = yaml.safe_load(f) or {}
    return jsonify({'language': lang, 'translations': translations})