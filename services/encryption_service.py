"""
Encryption Service
Handles encryption and decryption of sensitive data
"""

import os
import base64
import json
from typing import Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""

    def __init__(self):
        # Get or generate encryption key
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)

        # For field-level encryption
        self.field_key = self._derive_field_key()
        self.aesgcm = AESGCM(self.field_key)

    def _get_or_create_master_key(self) -> bytes:
        """Get master encryption key from environment or create one"""
        key_string = os.getenv("ENCRYPTION_KEY")

        if key_string:
            # Decode from base64
            return base64.b64decode(key_string)
        else:
            # Generate new key (should be stored securely!)
            key = Fernet.generate_key()
            logger.warning(f"Generated new encryption key. Store this securely: {base64.b64encode(key).decode()}")
            return key

    def _derive_field_key(self) -> bytes:
        """Derive a key for field-level encryption"""
        salt = b"weathercraft_field_salt_v1"  # Should be stored securely
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self.master_key[:32])

    def encrypt(self, data: str) -> str:
        """Encrypt a string value"""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string"""
        try:
            decoded = base64.b64decode(encrypted_data)
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary (JSON serialize first)"""
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt to dictionary"""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)

    def encrypt_field(self, value: Any, field_name: str = "") -> str:
        """Encrypt a specific field with additional context"""
        # Convert to string if needed
        str_value = json.dumps(value) if not isinstance(value, str) else value

        # Create nonce for this encryption
        nonce = os.urandom(12)

        # Add field name as additional data for authentication
        aad = field_name.encode()

        # Encrypt
        ciphertext = self.aesgcm.encrypt(nonce, str_value.encode(), aad)

        # Combine nonce and ciphertext
        combined = nonce + ciphertext

        # Return base64 encoded
        return base64.b64encode(combined).decode()

    def decrypt_field(self, encrypted_value: str, field_name: str = "") -> Any:
        """Decrypt a field value"""
        try:
            # Decode from base64
            combined = base64.b64decode(encrypted_value)

            # Extract nonce and ciphertext
            nonce = combined[:12]
            ciphertext = combined[12:]

            # Decrypt with field name as additional data
            aad = field_name.encode()
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, aad)

            # Try to parse as JSON, otherwise return as string
            str_value = plaintext.decode()
            try:
                return json.loads(str_value)
            except json.JSONDecodeError:
                return str_value

        except Exception as e:
            logger.error(f"Field decryption failed: {e}")
            raise

    def hash_value(self, value: str, salt: str = "") -> str:
        """Create a one-way hash of a value (for searching)"""
        salted = f"{salt}{value}weathercraft"
        return hashlib.sha256(salted.encode()).hexdigest()

    def mask_sensitive_data(self, data: str, visible_chars: int = 4) -> str:
        """Mask sensitive data for display (e.g., SSN: ***-**-1234)"""
        if len(data) <= visible_chars:
            return "*" * len(data)

        masked_length = len(data) - visible_chars
        return "*" * masked_length + data[-visible_chars:]

    def tokenize(self, sensitive_value: str) -> str:
        """Create a token that can be used to reference sensitive data"""
        # Create a unique token
        timestamp = str(datetime.utcnow().timestamp())
        token_data = f"{sensitive_value}{timestamp}{os.urandom(8).hex()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()

        # Store mapping (in production, use secure vault)
        # This is simplified - use proper vault service in production
        return f"tok_{token[:32]}"

# Singleton instance
encryption_service = EncryptionService()

# Field definitions for automatic encryption
ENCRYPTED_FIELDS = {
    "customers": ["ssn", "tax_id", "bank_account"],
    "employees": ["ssn", "salary", "bank_details"],
    "invoices": ["payment_details"],
    "users": ["phone", "address"],
}

def encrypt_model_fields(model_name: str, data: dict) -> dict:
    """Automatically encrypt designated fields in a model"""
    if model_name not in ENCRYPTED_FIELDS:
        return data

    encrypted_data = data.copy()
    for field in ENCRYPTED_FIELDS[model_name]:
        if field in encrypted_data and encrypted_data[field]:
            encrypted_data[field] = encryption_service.encrypt_field(
                encrypted_data[field],
                field_name=f"{model_name}.{field}"
            )

    return encrypted_data

def decrypt_model_fields(model_name: str, data: dict) -> dict:
    """Automatically decrypt designated fields in a model"""
    if model_name not in ENCRYPTED_FIELDS:
        return data

    decrypted_data = data.copy()
    for field in ENCRYPTED_FIELDS[model_name]:
        if field in decrypted_data and decrypted_data[field]:
            try:
                decrypted_data[field] = encryption_service.decrypt_field(
                    decrypted_data[field],
                    field_name=f"{model_name}.{field}"
                )
            except:
                # If decryption fails, likely not encrypted
                pass

    return decrypted_data

# Export main functions
encrypt = encryption_service.encrypt
decrypt = encryption_service.decrypt
encrypt_field = encryption_service.encrypt_field
decrypt_field = encryption_service.decrypt_field
hash_value = encryption_service.hash_value
mask_sensitive_data = encryption_service.mask_sensitive_data