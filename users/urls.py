from django.urls import path
from . import jwt_auth

urlpatterns = [
    path('login', jwt_auth.LoginView.as_view()),
    path('verify-token', jwt_auth.VerifyTokenView.as_view()),
    path('logout', jwt_auth.LogoutView.as_view())
]