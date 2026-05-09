"""
MediCore HMS — Root URL configuration.
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Django Admin 
    path("admin/", admin.site.urls),

    # Built-in Authentication 
    # LoginView  → /auth/login/
    # LogoutView → /auth/logout/
    path(
        "auth/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),

    path(
        "auth/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # Hospital app 
    path("", include("hospital.urls")),
]
