from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from .views import CustomLoginView
from . import fingerprint_views


app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'),
    path('fingerprint-login/', fingerprint_views.fingerprint_login, name='fingerprint_login'),
    path('register-fingerprint/', fingerprint_views.register_fingerprint, name='register_fingerprint'),
    # We can add password change, reset, and registration views here later if needed.
]