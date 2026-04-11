"""
predictor/utils.py
Utility functions and custom error handler.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Return consistent JSON error shape for all API errors."""
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': _flatten_errors(response.data),
            }
        }
    else:
        # Unhandled exception → 500
        logger.exception(f"Unhandled exception in {context.get('view')}: {exc}")
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 500,
                    'message': 'An internal server error occurred. Please try again.',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _flatten_errors(data):
    """Flatten DRF error dict into a readable string."""
    if isinstance(data, dict):
        msgs = []
        for key, val in data.items():
            if isinstance(val, list):
                msgs.append(f"{key}: {', '.join(str(v) for v in val)}")
            else:
                msgs.append(str(val))
        return ' | '.join(msgs)
    elif isinstance(data, list):
        return ', '.join(str(v) for v in data)
    return str(data)


def success_response(data, message='Success', status_code=200):
    return Response(
        {'success': True, 'message': message, 'data': data},
        status=status_code
    )
