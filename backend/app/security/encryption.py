"""
Advanced Encryption and Data Protection
End-to-end encryption for sensitive SAR mission data
"""
import os
import base64
import hashlib
import secrets
import logging
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import json

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Comprehensive encryption management system"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or self._generate_master_key()
        self._setup_encryption_keys()
        
        # Data classification levels
        self.classification_levels = {
            "PUBLIC": 0,      # No encryption required
            "INTERNAL": 1,    # Basic encryption
            "CONFIDENTIAL": 2, # Strong encryption
            "SECRET": 3,      # Maximum encryption
            "TOP_SECRET": 4   # Military-grade encryption
        }
    
    def _generate_master_key(self) -> str:
        """Generate master encryption key"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def _setup_encryption_keys(self):
        """Setup encryption keys for different classification levels"""
        self.keys = {}
        
        # Generate keys for each classification level
        for level in self.classification_levels:
            if level == "PUBLIC":
                self.keys[level] = None  # No encryption for public data
            else:
                # Generate Fernet key for symmetric encryption
                key = Fernet.generate_key()
                self.keys[level] = Fernet(key)
        
        # Generate RSA key pair for asymmetric encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
        logger.info("Encryption keys initialized")
    
    def encrypt_data(self, data: Union[str, bytes, Dict[str, Any]], 
                    classification: str = "CONFIDENTIAL") -> Dict[str, Any]:
        """Encrypt data based on classification level"""
        
        # Convert data to bytes
        if isinstance(data, dict):
            data_bytes = json.dumps(data, default=str).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
        
        # Check classification level
        if classification not in self.classification_levels:
            raise ValueError(f"Invalid classification level: {classification}")
        
        if classification == "PUBLIC":
            # No encryption for public data
            return {
                "encrypted": False,
                "data": base64.b64encode(data_bytes).decode(),
                "classification": classification,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get encryption key for classification level
        fernet = self.keys[classification]
        if not fernet:
            raise ValueError(f"No encryption key for classification: {classification}")
        
        # Encrypt data
        encrypted_data = fernet.encrypt(data_bytes)
        
        # Create metadata
        metadata = {
            "encrypted": True,
            "data": base64.b64encode(encrypted_data).decode(),
            "classification": classification,
            "algorithm": "AES-256-GCM",
            "timestamp": datetime.utcnow().isoformat(),
            "key_version": "1.0"
        }
        
        return metadata
    
    def decrypt_data(self, encrypted_metadata: Dict[str, Any]) -> Union[str, bytes, Dict[str, Any]]:
        """Decrypt data from metadata"""
        
        if not encrypted_metadata.get("encrypted", False):
            # Data is not encrypted
            data = base64.b64decode(encrypted_metadata["data"])
            return data.decode('utf-8') if encrypted_metadata.get("is_string", True) else data
        
        classification = encrypted_metadata.get("classification")
        if not classification or classification not in self.classification_levels:
            raise ValueError(f"Invalid or missing classification: {classification}")
        
        # Get decryption key
        fernet = self.keys[classification]
        if not fernet:
            raise ValueError(f"No decryption key for classification: {classification}")
        
        # Decrypt data
        encrypted_data = base64.b64decode(encrypted_metadata["data"])
        decrypted_data = fernet.decrypt(encrypted_data)
        
        return decrypted_data
    
    def encrypt_field(self, field_name: str, value: Any, 
                     classification: str = "CONFIDENTIAL") -> Dict[str, Any]:
        """Encrypt a specific field with metadata"""
        
        # Generate field-specific salt
        salt = os.urandom(16)
        
        # Derive key from master key and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        fernet = Fernet(key)
        
        # Convert value to bytes
        if isinstance(value, dict):
            value_bytes = json.dumps(value, default=str).encode('utf-8')
        elif isinstance(value, str):
            value_bytes = value.encode('utf-8')
        else:
            value_bytes = str(value).encode('utf-8')
        
        # Encrypt value
        encrypted_value = fernet.encrypt(value_bytes)
        
        return {
            "field": field_name,
            "encrypted_value": base64.b64encode(encrypted_value).decode(),
            "salt": base64.b64encode(salt).decode(),
            "classification": classification,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def decrypt_field(self, encrypted_field: Dict[str, Any]) -> Any:
        """Decrypt a specific field"""
        
        # Extract components
        encrypted_value = base64.b64decode(encrypted_field["encrypted_value"])
        salt = base64.b64decode(encrypted_field["salt"])
        
        # Derive key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        fernet = Fernet(key)
        
        # Decrypt value
        decrypted_bytes = fernet.decrypt(encrypted_value)
        
        # Try to decode as JSON first, then as string
        try:
            return json.loads(decrypted_bytes.decode('utf-8'))
        except json.JSONDecodeError:
            return decrypted_bytes.decode('utf-8')
    
    def encrypt_file(self, file_path: str, output_path: str, 
                    classification: str = "CONFIDENTIAL") -> bool:
        """Encrypt a file"""
        try:
            with open(file_path, 'rb') as infile:
                file_data = infile.read()
            
            encrypted_metadata = self.encrypt_data(file_data, classification)
            
            with open(output_path, 'w') as outfile:
                json.dump(encrypted_metadata, outfile)
            
            return True
            
        except Exception as e:
            logger.error(f"Error encrypting file {file_path}: {e}")
            return False
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str) -> bool:
        """Decrypt a file"""
        try:
            with open(encrypted_file_path, 'r') as infile:
                encrypted_metadata = json.load(infile)
            
            decrypted_data = self.decrypt_data(encrypted_metadata)
            
            with open(output_path, 'wb') as outfile:
                outfile.write(decrypted_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error decrypting file {encrypted_file_path}: {e}")
            return False
    
    def encrypt_database_record(self, record: Dict[str, Any], 
                               field_classifications: Dict[str, str]) -> Dict[str, Any]:
        """Encrypt database record fields based on classification"""
        encrypted_record = {}
        
        for field_name, value in record.items():
            classification = field_classifications.get(field_name, "PUBLIC")
            
            if classification == "PUBLIC":
                encrypted_record[field_name] = value
            else:
                encrypted_field = self.encrypt_field(field_name, value, classification)
                encrypted_record[f"{field_name}_encrypted"] = encrypted_field
        
        return encrypted_record
    
    def decrypt_database_record(self, encrypted_record: Dict[str, Any],
                               field_classifications: Dict[str, str]) -> Dict[str, Any]:
        """Decrypt database record fields"""
        decrypted_record = {}
        
        for field_name in field_classifications.keys():
            encrypted_field_key = f"{field_name}_encrypted"
            
            if encrypted_field_key in encrypted_record:
                # Field is encrypted
                encrypted_field = encrypted_record[encrypted_field_key]
                decrypted_record[field_name] = self.decrypt_field(encrypted_field)
            elif field_name in encrypted_record:
                # Field is not encrypted
                decrypted_record[field_name] = encrypted_record[field_name]
        
        return decrypted_record
    
    def generate_secure_hash(self, data: Union[str, bytes], salt: Optional[str] = None) -> str:
        """Generate secure hash with salt"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Combine data and salt
        combined = data + salt.encode('utf-8')
        
        # Generate hash
        hash_obj = hashlib.sha256(combined)
        
        # Return salt and hash
        return f"{salt}:{hash_obj.hexdigest()}"
    
    def verify_secure_hash(self, data: Union[str, bytes], hash_string: str) -> bool:
        """Verify secure hash"""
        try:
            salt, expected_hash = hash_string.split(':', 1)
            
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            combined = data + salt.encode('utf-8')
            actual_hash = hashlib.sha256(combined).hexdigest()
            
            return actual_hash == expected_hash
            
        except Exception:
            return False
    
    def encrypt_communication(self, message: str, recipient_public_key: bytes) -> Dict[str, Any]:
        """Encrypt message for secure communication"""
        
        # Load recipient's public key
        public_key = serialization.load_pem_public_key(
            recipient_public_key,
            backend=default_backend()
        )
        
        # Generate session key
        session_key = os.urandom(32)
        
        # Encrypt session key with recipient's public key
        encrypted_session_key = public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Encrypt message with session key
        fernet = Fernet(base64.urlsafe_b64encode(session_key))
        encrypted_message = fernet.encrypt(message.encode('utf-8'))
        
        return {
            "encrypted_session_key": base64.b64encode(encrypted_session_key).decode(),
            "encrypted_message": base64.b64encode(encrypted_message).decode(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def decrypt_communication(self, encrypted_data: Dict[str, Any]) -> str:
        """Decrypt received communication"""
        
        # Decrypt session key with private key
        encrypted_session_key = base64.b64decode(encrypted_data["encrypted_session_key"])
        session_key = self.private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Decrypt message with session key
        fernet = Fernet(base64.urlsafe_b64encode(session_key))
        encrypted_message = base64.b64decode(encrypted_data["encrypted_message"])
        decrypted_message = fernet.decrypt(encrypted_message)
        
        return decrypted_message.decode('utf-8')
    
    def export_public_key(self) -> bytes:
        """Export public key for sharing"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def rotate_encryption_keys(self):
        """Rotate encryption keys for enhanced security"""
        logger.info("Rotating encryption keys...")
        
        # Generate new keys for each classification level
        for level in self.classification_levels:
            if level != "PUBLIC":
                key = Fernet.generate_key()
                self.keys[level] = Fernet(key)
        
        logger.info("Encryption keys rotated successfully")
    
    def get_key_status(self) -> Dict[str, Any]:
        """Get encryption key status and statistics"""
        return {
            "classification_levels": list(self.classification_levels.keys()),
            "keys_initialized": len([k for k in self.keys.values() if k is not None]),
            "public_key_available": self.public_key is not None,
            "private_key_available": self.private_key is not None,
            "last_key_rotation": datetime.utcnow().isoformat()
        }

class DataClassificationManager:
    """Manage data classification and encryption policies"""
    
    def __init__(self):
        self.classification_policies = {
            "mission_data": {
                "mission_id": "PUBLIC",
                "mission_name": "INTERNAL",
                "mission_type": "INTERNAL",
                "search_area": "CONFIDENTIAL",
                "mission_plan": "CONFIDENTIAL",
                "participants": "CONFIDENTIAL",
                "results": "SECRET"
            },
            "drone_data": {
                "drone_id": "PUBLIC",
                "model": "INTERNAL",
                "serial_number": "CONFIDENTIAL",
                "location": "CONFIDENTIAL",
                "telemetry": "CONFIDENTIAL",
                "mission_data": "SECRET"
            },
            "discovery_data": {
                "discovery_id": "PUBLIC",
                "discovery_type": "CONFIDENTIAL",
                "location": "CONFIDENTIAL",
                "confidence": "CONFIDENTIAL",
                "images": "SECRET",
                "metadata": "SECRET"
            },
            "user_data": {
                "user_id": "PUBLIC",
                "username": "INTERNAL",
                "email": "CONFIDENTIAL",
                "full_name": "CONFIDENTIAL",
                "password_hash": "SECRET",
                "mfa_secret": "TOP_SECRET"
            }
        }
    
    def get_field_classification(self, data_type: str, field_name: str) -> str:
        """Get classification level for a specific field"""
        if data_type in self.classification_policies:
            return self.classification_policies[data_type].get(field_name, "CONFIDENTIAL")
        return "CONFIDENTIAL"  # Default classification
    
    def get_data_type_classifications(self, data_type: str) -> Dict[str, str]:
        """Get all field classifications for a data type"""
        return self.classification_policies.get(data_type, {})
    
    def add_data_type_policy(self, data_type: str, field_classifications: Dict[str, str]):
        """Add classification policy for a new data type"""
        self.classification_policies[data_type] = field_classifications
    
    def update_field_classification(self, data_type: str, field_name: str, classification: str):
        """Update classification for a specific field"""
        if data_type not in self.classification_policies:
            self.classification_policies[data_type] = {}
        
        self.classification_policies[data_type][field_name] = classification

# Global encryption manager instance
encryption_manager = EncryptionManager()

# Global data classification manager instance
classification_manager = DataClassificationManager()
