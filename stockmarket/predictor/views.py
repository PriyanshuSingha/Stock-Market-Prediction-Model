"""
predictor/views.py
API views: Register, Login, Predict, History.
"""

import logging
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PredictionHistory, SearchLog
from .serializers import RegisterSerializer, UserSerializer, PredictionHistorySerializer
from .services.predictor import run_prediction
from .utils import success_response

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Auth Views
# ─────────────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    """POST /api/register/ — Create a new user account."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        logger.info(f"New user registered: {user.username}")
        return success_response(
            {
                'user': UserSerializer(user).data,
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
            },
            message='Account created successfully.',
            status_code=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/login/ — Authenticate and get JWT tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'success': False, 'error': {'message': 'Username and password are required.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)

        if not user:
            logger.warning(f"Failed login attempt for username: {username}")
            return Response(
                {'success': False, 'error': {'message': 'Invalid credentials. Please try again.'}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        logger.info(f"User logged in: {username}")

        return success_response(
            {
                'user': UserSerializer(user).data,
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
            },
            message='Login successful.',
        )


class LogoutView(APIView):
    """POST /api/logout/ — Blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass  # Token already invalid — that's fine

        return success_response({}, message='Logged out successfully.')


class UserProfileView(APIView):
    """GET /api/me/ — Current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(UserSerializer(request.user).data)


# ─────────────────────────────────────────────────────────────────────────────
# Prediction Views
# ─────────────────────────────────────────────────────────────────────────────

class PredictView(APIView):
    """
    GET /api/predict/?symbol=AAPL&model=linear&days=7
    Main prediction endpoint — fetches data, trains model, returns forecast.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        symbol         = request.query_params.get('symbol', '').strip().upper()
        model_type     = request.query_params.get('model', 'linear').lower()
        prediction_days = int(request.query_params.get('days', 7))

        # ── Validate inputs ───────────────────────────────────────────────────
        if not symbol:
            return Response(
                {'success': False, 'error': {'message': 'Stock symbol is required. e.g. ?symbol=AAPL'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if prediction_days < 1 or prediction_days > 30:
            return Response(
                {'success': False, 'error': {'message': 'Prediction days must be between 1 and 30.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Log search ────────────────────────────────────────────────────────
        search_log = SearchLog(user=request.user, symbol=symbol)

        try:
            result = run_prediction(symbol, model_type, prediction_days)

            # ── Save to history ───────────────────────────────────────────────
            metrics = result.get('metrics', {})
            PredictionHistory.objects.create(
                user            = request.user,
                symbol          = symbol,
                company_name    = result.get('company_name', ''),
                model_used      = model_type,
                current_price   = result.get('current_price'),
                price_change_pct= result.get('price_change_pct'),
                r2_score        = metrics.get('r2_score'),
                mse             = metrics.get('mse'),
                rmse            = metrics.get('rmse'),
                prediction_days = prediction_days,
            )

            search_log.success = True
            search_log.save()

            return success_response(result, message='Prediction completed successfully.')

        except ValueError as e:
            search_log.success = False
            search_log.error_message = str(e)
            search_log.save()
            return Response(
                {'success': False, 'error': {'message': str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ImportError as e:
            return Response(
                {'success': False, 'error': {'message': str(e)}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.exception(f"Unexpected error in PredictView for {symbol}: {e}")
            search_log.success = False
            search_log.error_message = str(e)
            search_log.save()
            return Response(
                {'success': False, 'error': {'message': 'An error occurred while processing your request.'}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PredictionHistoryView(APIView):
    """GET /api/history/ — Return last 20 predictions for current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        predictions = PredictionHistory.objects.filter(user=request.user)[:20]
        serializer  = PredictionHistorySerializer(predictions, many=True)
        return success_response(serializer.data)


class PopularStocksView(APIView):
    """GET /api/popular/ — Return a curated list of popular tickers."""
    permission_classes = [AllowAny]

    POPULAR = [
        {'symbol': 'AAPL',  'name': 'Apple Inc.'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'MSFT',  'name': 'Microsoft Corp.'},
        {'symbol': 'TSLA',  'name': 'Tesla Inc.'},
        {'symbol': 'AMZN',  'name': 'Amazon.com Inc.'},
        {'symbol': 'NVDA',  'name': 'NVIDIA Corp.'},
        {'symbol': 'META',  'name': 'Meta Platforms'},
        {'symbol': 'NFLX',  'name': 'Netflix Inc.'},
    ]

    def get(self, request):
        return success_response(self.POPULAR)
