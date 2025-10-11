"""
Comprehensive Security Framework
Authentication, Authorization, and Security Controls for SAR Drone System
"""
import hashlib
import secrets
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import pyotp
import qrcode
from io import BytesIO
import base64
import uuid
from functools import wraps

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles in the system"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    DRONE_PILOT = "drone_pilot"
    MISSION_COORDINATOR = "mission_coordinator"
    TECHNICIAN = "technician"
    EMERGENCY_RESPONDER = "emergency_responder"

class Permission(Enum):
    """System permissions"""
    # User management
    CREATE_USERS = "create_users"
    READ_USERS = "read_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    
    # Mission management
    CREATE_MISSIONS = "create_missions"
    READ_MISSIONS = "read_missions"
    UPDATE_MISSIONS = "update_missions"
    DELETE_MISSIONS = "delete_missions"
    EXECUTE_MISSIONS = "execute_missions"
    
    # Drone management
    CREATE_DRONES = "create_drones"
    READ_DRONES = "read_drones"
    UPDATE_DRONES = "update_drones"
    DELETE_DRONES = "delete_drones"
    CONTROL_DRONES = "control_drones"
    
    # Discovery management
    READ_DISCOVERIES = "read_discoveries"
    UPDATE_DISCOVERIES = "update_discoveries"
    DELETE_DISCOVERIES = "delete_discoveries"
    
    # System administration
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MANAGE_SYSTEM_CONFIG = "manage_system_config"
    VIEW_METRICS = "view_metrics"
    MANAGE_ALERTS = "manage_alerts"
    
    # Emergency procedures
    DECLARE_EMERGENCY = "declare_emergency"
    EMERGENCY_OVERRIDE = "emergency_override"
    ACCESS_EMERGENCY_DATA = "access_emergency_data"

@dataclass
class User:
    """User model"""
    id: str
    username: str
    email: str
    full_name: str
    roles: List[UserRole]
    permissions: List[Permission]
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    password_hash: str = ""
    mfa_secret: Optional[str] = None
    mfa_enabled: bool = False
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    api_keys: List[str] = field(default_factory=list)
    session_tokens: List[str] = field(default_factory=list)

@dataclass
class Session:
    """User session"""
    id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True

@dataclass
class SecurityEvent:
    """Security event log"""
    id: str
    event_type: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: str = "info"

class RolePermissions:
    """Role-based permission mapping"""
    
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            Permission.CREATE_USERS,
            Permission.READ_USERS,
            Permission.UPDATE_USERS,
            Permission.DELETE_USERS,
            Permission.CREATE_MISSIONS,
            Permission.READ_MISSIONS,
            Permission.UPDATE_MISSIONS,
            Permission.DELETE_MISSIONS,
            Permission.EXECUTE_MISSIONS,
            Permission.CREATE_DRONES,
            Permission.READ_DRONES,
            Permission.UPDATE_DRONES,
            Permission.DELETE_DRONES,
            Permission.CONTROL_DRONES,
            Permission.READ_DISCOVERIES,
            Permission.UPDATE_DISCOVERIES,
            Permission.DELETE_DISCOVERIES,
            Permission.VIEW_SYSTEM_LOGS,
            Permission.MANAGE_SYSTEM_CONFIG,
            Permission.VIEW_METRICS,
            Permission.MANAGE_ALERTS,
            Permission.DECLARE_EMERGENCY,
            Permission.EMERGENCY_OVERRIDE,
            Permission.ACCESS_EMERGENCY_DATA,
        ],
        UserRole.OPERATOR: [
            Permission.READ_MISSIONS,
            Permission.UPDATE_MISSIONS,
            Permission.EXECUTE_MISSIONS,
            Permission.READ_DRONES,
            Permission.CONTROL_DRONES,
            Permission.READ_DISCOVERIES,
            Permission.UPDATE_DISCOVERIES,
            Permission.VIEW_METRICS,
            Permission.DECLARE_EMERGENCY,
            Permission.ACCESS_EMERGENCY_DATA,
        ],
        UserRole.MISSION_COORDINATOR: [
            Permission.CREATE_MISSIONS,
            Permission.READ_MISSIONS,
            Permission.UPDATE_MISSIONS,
            Permission.EXECUTE_MISSIONS,
            Permission.READ_DRONES,
            Permission.READ_DISCOVERIES,
            Permission.UPDATE_DISCOVERIES,
            Permission.VIEW_METRICS,
            Permission.DECLARE_EMERGENCY,
            Permission.ACCESS_EMERGENCY_DATA,
        ],
        UserRole.DRONE_PILOT: [
            Permission.READ_MISSIONS,
            Permission.READ_DRONES,
            Permission.CONTROL_DRONES,
            Permission.READ_DISCOVERIES,
            Permission.VIEW_METRICS,
        ],
        UserRole.TECHNICIAN: [
            Permission.READ_DRONES,
            Permission.UPDATE_DRONES,
            Permission.READ_DISCOVERIES,
            Permission.VIEW_SYSTEM_LOGS,
            Permission.VIEW_METRICS,
        ],
        UserRole.EMERGENCY_RESPONDER: [
            Permission.READ_MISSIONS,
            Permission.READ_DISCOVERIES,
            Permission.ACCESS_EMERGENCY_DATA,
            Permission.DECLARE_EMERGENCY,
        ],
        UserRole.VIEWER: [
            Permission.READ_MISSIONS,
            Permission.READ_DRONES,
            Permission.READ_DISCOVERIES,
            Permission.VIEW_METRICS,
        ],
    }
    
    @classmethod
    def get_permissions_for_role(cls, role: UserRole) -> List[Permission]:
        """Get permissions for a specific role"""
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def get_permissions_for_roles(cls, roles: List[UserRole]) -> List[Permission]:
        """Get permissions for multiple roles"""
        permissions = set()
        for role in roles:
            permissions.update(cls.get_permissions_for_role(role))
        return list(permissions)

class SecurityManager:
    """Comprehensive security management system"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # In-memory storage (in production, use database)
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.security_events: List[SecurityEvent] = []
        self.blocked_ips: Dict[str, datetime] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        
        # Security settings
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        self.session_timeout = timedelta(hours=8)
        self.api_key_expiry = timedelta(days=90)
        self.rate_limit_window = timedelta(minutes=1)
        self.max_requests_per_window = 100
        
        # Initialize default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user"""
        admin_id = str(uuid.uuid4())
        admin_user = User(
            id=admin_id,
            username="admin",
            email="admin@sardrone.com",
            full_name="System Administrator",
            roles=[UserRole.ADMIN],
            permissions=RolePermissions.get_permissions_for_role(UserRole.ADMIN),
            is_active=True,
            is_verified=True,
            password_hash=self._hash_password("admin123!@#"),
            mfa_enabled=False
        )
        self.users[admin_id] = admin_user
        logger.info("Default admin user created")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def _generate_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Generate JWT token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + self.session_timeout
        
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access_token"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def _generate_api_key(self) -> str:
        """Generate API key"""
        return secrets.token_urlsafe(32)
    
    def _generate_mfa_secret(self) -> str:
        """Generate MFA secret"""
        return pyotp.random_base32()
    
    def _log_security_event(self, event_type: str, user_id: Optional[str], 
                          ip_address: str, user_agent: str, details: Dict[str, Any],
                          severity: str = "info"):
        """Log security event"""
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            severity=severity
        )
        self.security_events.append(event)
        
        # Keep only last 1000 events
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
        
        logger.info(f"Security event: {event_type} - {details}")
    
    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check rate limiting for IP address"""
        current_time = datetime.utcnow()
        window_start = current_time - self.rate_limit_window
        
        # Clean old requests
        if ip_address in self.rate_limits:
            self.rate_limits[ip_address] = [
                req_time for req_time in self.rate_limits[ip_address]
                if req_time > window_start
            ]
        else:
            self.rate_limits[ip_address] = []
        
        # Check limit
        if len(self.rate_limits[ip_address]) >= self.max_requests_per_window:
            return False
        
        # Add current request
        self.rate_limits[ip_address].append(current_time)
        return True
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        if ip_address in self.blocked_ips:
            block_until = self.blocked_ips[ip_address]
            if datetime.utcnow() < block_until:
                return True
            else:
                del self.blocked_ips[ip_address]
        return False
    
    def _block_ip(self, ip_address: str, duration: timedelta = timedelta(hours=1)):
        """Block IP address"""
        self.blocked_ips[ip_address] = datetime.utcnow() + duration
        logger.warning(f"IP address {ip_address} blocked for {duration}")
    
    def authenticate_user(self, username: str, password: str, 
                         mfa_code: Optional[str] = None,
                         ip_address: str = "unknown",
                         user_agent: str = "unknown") -> Tuple[Optional[User], str]:
        """Authenticate user with username and password"""
        
        # Check rate limiting
        if not self._check_rate_limit(ip_address):
            self._log_security_event("rate_limit_exceeded", None, ip_address, user_agent,
                                   {"username": username}, "warning")
            return None, "Rate limit exceeded"
        
        # Check if IP is blocked
        if self._is_ip_blocked(ip_address):
            self._log_security_event("blocked_ip_access", None, ip_address, user_agent,
                                   {"username": username}, "warning")
            return None, "IP address is blocked"
        
        # Find user by username
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            self._log_security_event("login_failed", None, ip_address, user_agent,
                                   {"username": username, "reason": "user_not_found"}, "info")
            return None, "Invalid credentials"
        
        # Check if user is active
        if not user.is_active:
            self._log_security_event("login_failed", user.id, ip_address, user_agent,
                                   {"username": username, "reason": "account_disabled"}, "warning")
            return None, "Account is disabled"
        
        # Check if account is locked
        if user.locked_until and datetime.utcnow() < user.locked_until:
            self._log_security_event("login_failed", user.id, ip_address, user_agent,
                                   {"username": username, "reason": "account_locked"}, "warning")
            return None, "Account is temporarily locked"
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            # Lock account after max attempts
            if user.failed_login_attempts >= self.max_login_attempts:
                user.locked_until = datetime.utcnow() + self.lockout_duration
                self._log_security_event("account_locked", user.id, ip_address, user_agent,
                                       {"username": username, "attempts": user.failed_login_attempts}, "warning")
                return None, "Account locked due to too many failed attempts"
            
            self._log_security_event("login_failed", user.id, ip_address, user_agent,
                                   {"username": username, "reason": "invalid_password", 
                                    "attempts": user.failed_login_attempts}, "info")
            return None, "Invalid credentials"
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not mfa_code:
                self._log_security_event("mfa_required", user.id, ip_address, user_agent,
                                       {"username": username}, "info")
                return None, "MFA code required"
            
            if not self._verify_mfa_code(user, mfa_code):
                self._log_security_event("mfa_failed", user.id, ip_address, user_agent,
                                       {"username": username}, "warning")
                return None, "Invalid MFA code"
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        
        self._log_security_event("login_success", user.id, ip_address, user_agent,
                               {"username": username}, "info")
        
        return user, "Authentication successful"
    
    def create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        """Create user session"""
        session_id = str(uuid.uuid4())
        token = self._generate_token(user.id)
        
        session = Session(
            id=session_id,
            user_id=user.id,
            token=token,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.session_timeout,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        user.session_tokens.append(token)
        
        self._log_security_event("session_created", user.id, ip_address, user_agent,
                               {"session_id": session_id}, "info")
        
        return session
    
    def verify_session(self, token: str) -> Optional[Session]:
        """Verify session token"""
        payload = self._verify_token(token)
        if not payload:
            return None
        
        # Find session
        for session in self.sessions.values():
            if session.token == token and session.is_active:
                if datetime.utcnow() < session.expires_at:
                    return session
                else:
                    session.is_active = False
        
        return None
    
    def logout_session(self, token: str, ip_address: str = "unknown"):
        """Logout session"""
        for session in self.sessions.values():
            if session.token == token:
                session.is_active = False
                self._log_security_event("session_logout", session.user_id, ip_address, "unknown",
                                       {"session_id": session.id}, "info")
                break
    
    def create_user(self, username: str, email: str, full_name: str, 
                   password: str, roles: List[UserRole], 
                   creator_user_id: str) -> Optional[User]:
        """Create new user"""
        # Check if user already exists
        for user in self.users.values():
            if user.username == username or user.email == email:
                return None
        
        # Verify creator has permission
        creator = self.users.get(creator_user_id)
        if not creator or Permission.CREATE_USERS not in creator.permissions:
            return None
        
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            roles=roles,
            permissions=RolePermissions.get_permissions_for_roles(roles),
            password_hash=self._hash_password(password),
            mfa_secret=self._generate_mfa_secret()
        )
        
        self.users[user_id] = user
        
        self._log_security_event("user_created", creator_user_id, "system", "system",
                               {"created_user_id": user_id, "username": username, "roles": [r.value for r in roles]}, "info")
        
        return user
    
    def generate_api_key(self, user_id: str) -> Optional[str]:
        """Generate API key for user"""
        user = self.users.get(user_id)
        if not user:
            return None
        
        api_key = self._generate_api_key()
        user.api_keys.append(api_key)
        
        self._log_security_event("api_key_generated", user_id, "system", "system",
                               {"api_key": api_key[:8] + "..."}, "info")
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[User]:
        """Verify API key"""
        for user in self.users.values():
            if api_key in user.api_keys:
                return user
        return None
    
    def setup_mfa(self, user_id: str) -> Tuple[str, str]:
        """Setup MFA for user and return secret and QR code"""
        user = self.users.get(user_id)
        if not user or user.mfa_enabled:
            return None, None
        
        user.mfa_secret = self._generate_mfa_secret()
        
        # Generate QR code
        totp_uri = pyotp.totp.TOTP(user.mfa_secret).provisioning_uri(
            name=user.email,
            issuer_name="SAR Drone System"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        self._log_security_event("mfa_setup", user_id, "system", "system", {}, "info")
        
        return user.mfa_secret, qr_code_b64
    
    def enable_mfa(self, user_id: str, mfa_code: str) -> bool:
        """Enable MFA after verification"""
        user = self.users.get(user_id)
        if not user or not user.mfa_secret:
            return False
        
        if self._verify_mfa_code(user, mfa_code):
            user.mfa_enabled = True
            self._log_security_event("mfa_enabled", user_id, "system", "system", {}, "info")
            return True
        
        return False
    
    def _verify_mfa_code(self, user: User, mfa_code: str) -> bool:
        """Verify MFA code"""
        if not user.mfa_secret:
            return False
        
        totp = pyotp.TOTP(user.mfa_secret)
        return totp.verify(mfa_code)
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        return permission in user.permissions
    
    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for user"""
        user = self.users.get(user_id)
        if not user:
            return []
        
        return user.permissions
    
    def get_security_events(self, limit: int = 100) -> List[SecurityEvent]:
        """Get recent security events"""
        return self.security_events[-limit:]
    
    def get_active_sessions(self) -> List[Session]:
        """Get all active sessions"""
        return [session for session in self.sessions.values() if session.is_active]

# Global security manager instance
security_manager = SecurityManager("your-secret-key-here")

# Decorator for authentication
def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This would be implemented in the actual FastAPI route
        # For now, it's a placeholder
        return f(*args, **kwargs)
    return decorated_function

# Decorator for permission checking
def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would be implemented in the actual FastAPI route
            # For now, it's a placeholder
            return f(*args, **kwargs)
        return decorated_function
    return decorator
