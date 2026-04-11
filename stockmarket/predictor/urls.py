"""
predictor/urls.py
URL routing for all API endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
    # ── Auth ──────────────────────────────────────────────────────────────────
path('register/', views.RegisterView.as_view(),    name='register'),

urlpatterns = [path('register/', views.RegisterView.as_view(),    name='register'),
    path('login/',    views.LoginView.as_view(),        name='login'),
    path('logout/',   views.LogoutView.as_view(),       name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/',       views.UserProfileView.as_view(),  name='user_profile'),

    # ── Prediction ────────────────────────────────────────────────────────────
    path('predict/', views.PredictView.as_view(),           name='predict'),
    path('history/', views.PredictionHistoryView.as_view(), name='history'),
    path('popular/', views.PopularStocksView.as_view(),     name='popular'),
]
