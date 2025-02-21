from django.urls import path
from . import jwt

urlpatterns = [
    path('login', jwt.LoginView.as_view()),
    path('verify-token', jwt.VerifyTokenView.as_view()),
    path('logout', jwt.LogoutView.as_view())
]