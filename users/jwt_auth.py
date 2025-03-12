from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.conf import settings
import jwt

# Login View
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

# Verify Token
class VerifyTokenView(APIView):
    permission_classes = [permissions.AllowAny]  # Allow access without authentication

    def get(self, request):
        auth = JWTAuthentication()
        header = request.headers.get("Authorization")

        if not header:
            return Response({"error": "Token missing"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = header.split(" ")[1]  # Extract token from "Bearer <token>"
            validated_token = auth.get_validated_token(token)
            user = auth.get_user(validated_token)
            return Response({"message": "Token is valid", "user": user.username})
        except InvalidToken:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)


# Logout View
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"error": "No refresh token provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # ✅ This invalidates the token
            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)

        except Exception as e:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

# Register View
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password)
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

class JWTAuthenticationMixin:
    def verify_jwt_token(self, request):
        """
        Verifies the JWT token from the request headers.
        Returns the decoded payload if valid, otherwise None.
        """
        token = request.headers.get('Authorization')
        if not token:
            return None

        # The token is expected to be in the format: 'Bearer <token>'
        try:
            token = token.split()[1]  # Get the actual token from the 'Bearer <token>' format
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    def dispatch(self, request, *args, **kwargs):
        """
        Overriding dispatch to check JWT token before proceeding with the view logic.
        """
        payload = self.verify_jwt_token(request)

        if payload is None:
            return Response(
                {"detail": "Unauthorized Access"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Optionally, add the user info or token details to the request
        request.user = payload.get('user', None)
        
        return super().dispatch(request, *args, **kwargs)