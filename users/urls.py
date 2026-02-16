from django.urls import path
from .views import RegisterView, MeView, LogoutView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/me/', MeView.as_view(), name='api-me'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout')
]