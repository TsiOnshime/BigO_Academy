import jwt
from django.conf import settings
from rest_framework.response import Response


class JWTAuthMixin:
    
    def get_current_user(self, request) -> dict | None:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        try: 
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        
    def require_auth(self, request) -> dict | Response:
        user = self.get_current_user(request)
        if user is None:
            return Response(
                {"status": 401, "error": "UNAUTHORIZED",
                "message": "Authentication token is missing or invalid"},
                status=401
            )
        return user
    
    def require_admin(self, request) -> dict | Response:
        user = self.require_auth(request)
        if isinstance(user, Response):
            return user
        if user.get("role") != "ADMIN":
            return Response(
                {"status": 403, "error": "FORBIDDEN",
                "message": "You do not have permission"},
                status=403,
            )
        return user
    
    def require_teacher_or_admin(self, request) -> dict | Response:
        user = self.require_auth(request)
        if isinstance(user, Response):
            return user
        if user.get("role") not in ["TEACHER", "ADMIN"]:
            return Response(
                {"status": 403, "error": "FORBIDDEN",
                "message": "Teachers and Admins only"},
                status=403,
            )
        return user
    def require_admin_or_self(self, request, target_id: str) -> dict | Response:
        user = self.require_auth(request)
        if isinstance(user, Response):
            return user
        if user.get("role") == "ADMIN":
            return user
        if str(user.get("userId")) == str(target_id):
            return user
        
        return Response(
            {"status": 403, "error": "FORBIDDEN",
            "message": "You can only access your own analytics"},
            status=403
        )