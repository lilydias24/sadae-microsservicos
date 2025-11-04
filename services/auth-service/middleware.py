from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from auth import verify_token
from models import UserRole

class AuthMiddleware:
    """Authentication middleware for protecting routes"""
    
    def __init__(self, required_roles: list[UserRole] = None):
        self.required_roles = required_roles or []
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request):
        """Middleware function to check authentication"""
        
        # Skip authentication for public routes
        public_routes = ["/", "/health", "/docs", "/openapi.json", "/register"]
        if request.url.path in public_routes:
            return
        
        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        # Extract token
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        # Verify token
        try:
            payload = verify_token(token)
            user_role = payload.get("role")
            
            # Check role permissions
            if self.required_roles and user_role not in self.required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # Add user info to request state
            request.state.user = payload
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

def create_role_middleware(required_roles: list[UserRole]):
    """Factory function to create role-based middleware"""
    return AuthMiddleware(required_roles)
