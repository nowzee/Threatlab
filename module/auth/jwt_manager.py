import jwt
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from module.database.db_manager import DatabaseManagerUser

class JWTManager:
    """
    JWT Token Manager for secure authentication with access and refresh tokens
    """
    
    def __init__(self):
        # Load or generate JWT secret key
        self.secret_key = self._get_or_create_jwt_secret()
        self.access_token_expiry = 15 * 60  # 15 minutes
        self.refresh_token_expiry = 7 * 24 * 60 * 60  # 7 days
        self.algorithm = 'HS256'
    
    def _get_or_create_jwt_secret(self) -> str:
        """
        Get existing JWT secret or create a new one
        
        Returns:
            str: JWT secret key
        """
        try:
            with open('.jwt_secret', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            # Generate new secret key
            secret = secrets.token_urlsafe(64)
            with open('.jwt_secret', 'w') as f:
                f.write(secret)
            return secret
    
    def generate_tokens(self, username: str, user_id: int) -> Dict[str, str]:
        """
        Generate access and refresh tokens for a user
        
        Args:
            username (str): Username
            user_id (int): User ID
            
        Returns:
            Dict[str, str]: Dictionary containing access_token and refresh_token
        """
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'sub': user_id,
            'username': username,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(seconds=self.access_token_expiry)
        }
        
        # Refresh token payload
        refresh_payload = {
            'sub': user_id,
            'username': username,
            'type': 'refresh',
            'iat': now,
            'exp': now + timedelta(seconds=self.refresh_token_expiry),
            'jti': secrets.token_hex(16)  # Unique token ID for revocation
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        # Store refresh token in database for revocation tracking
        self._store_refresh_token(user_id, refresh_payload['jti'], refresh_payload['exp'])
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': self.access_token_expiry,
            'token_type': 'Bearer'
        }
    
    def verify_access_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode access token
        
        Args:
            token (str): JWT access token
            
        Returns:
            Optional[Dict]: Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get('type') != 'access':
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except (jwt.InvalidTokenError, jwt.DecodeError):
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode refresh token
        
        Args:
            token (str): JWT refresh token
            
        Returns:
            Optional[Dict]: Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get('type') != 'refresh':
                return None
            
            # Check if token is revoked
            if self._is_token_revoked(payload.get('jti')):
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except (jwt.InvalidTokenError, jwt.DecodeError):
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Generate new access token using refresh token
        
        Args:
            refresh_token (str): Valid refresh token
            
        Returns:
            Optional[Dict[str, str]]: New access token info or None if invalid
        """
        payload = self.verify_refresh_token(refresh_token)
        if not payload:
            return None
        
        # Generate new access token
        now = datetime.utcnow()
        access_payload = {
            'sub': payload['sub'],
            'username': payload['username'],
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(seconds=self.access_token_expiry)
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            'access_token': access_token,
            'expires_in': self.access_token_expiry,
            'token_type': 'Bearer'
        }
    
    def revoke_refresh_token(self, token: str) -> bool:
        """
        Revoke a refresh token
        
        Args:
            token (str): Refresh token to revoke
            
        Returns:
            bool: True if successfully revoked
        """
        payload = self.verify_refresh_token(token)
        if not payload:
            return False
        
        return self._revoke_token_by_jti(payload.get('jti'))
    
    def revoke_all_user_tokens(self, user_id: int) -> bool:
        """
        Revoke all refresh tokens for a user
        
        Args:
            user_id (int): User ID
            
        Returns:
            bool: True if successfully revoked
        """
        try:
            with DatabaseManagerUser() as db:
                db.execute("UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?", (user_id,))
            return True
        except Exception:
            return False
    
    def _store_refresh_token(self, user_id: int, jti: str, expiry: datetime) -> bool:
        """
        Store refresh token in database
        
        Args:
            user_id (int): User ID
            jti (str): Token unique ID
            expiry (datetime): Token expiry time
            
        Returns:
            bool: True if stored successfully
        """
        try:
            with DatabaseManagerUser() as db:
                # Create table if it doesn't exist
                db.execute('''
                    CREATE TABLE IF NOT EXISTS refresh_tokens (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        jti TEXT NOT NULL UNIQUE,
                        expiry DATETIME NOT NULL,
                        revoked INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                # Clean up expired tokens
                db.execute("DELETE FROM refresh_tokens WHERE expiry < ?", (datetime.utcnow(),))
                
                # Store new token
                db.execute(
                    "INSERT INTO refresh_tokens (user_id, jti, expiry) VALUES (?, ?, ?)",
                    (user_id, jti, expiry)
                )
            return True
        except Exception:
            return False
    
    def _is_token_revoked(self, jti: str) -> bool:
        """
        Check if token is revoked
        
        Args:
            jti (str): Token unique ID
            
        Returns:
            bool: True if token is revoked
        """
        try:
            with DatabaseManagerUser() as db:
                db.execute("SELECT revoked FROM refresh_tokens WHERE jti = ?", (jti,))
                result = db.fetchone()
                return result and result[0] == 1
        except Exception:
            return True  # Assume revoked if database error
    
    def _revoke_token_by_jti(self, jti: str) -> bool:
        """
        Revoke token by JTI
        
        Args:
            jti (str): Token unique ID
            
        Returns:
            bool: True if revoked successfully
        """
        try:
            with DatabaseManagerUser() as db:
                db.execute("UPDATE refresh_tokens SET revoked = 1 WHERE jti = ?", (jti,))
            return True
        except Exception:
            return False
    
    def cleanup_expired_tokens(self) -> bool:
        """
        Clean up expired refresh tokens from database
        
        Returns:
            bool: True if cleanup successful
        """
        try:
            with DatabaseManagerUser() as db:
                db.execute("DELETE FROM refresh_tokens WHERE expiry < ?", (datetime.utcnow(),))
            return True
        except Exception:
            return False