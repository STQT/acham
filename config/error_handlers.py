"""Custom error handlers that return JSON responses instead of HTML.

This is useful for API/backend projects where clients expect JSON responses.
"""
import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def handler400(request, exception=None):
    """Handle 400 Bad Request errors with JSON response."""
    return JsonResponse(
        {
            "error": "Bad Request",
            "status_code": 400,
            "message": "The request could not be understood by the server due to malformed syntax.",
        },
        status=400,
    )


def handler403(request, exception=None):
    """Handle 403 Forbidden errors with JSON response."""
    message = "You do not have permission to perform this action."
    if exception:
        message = str(exception) if str(exception) else message
    
    return JsonResponse(
        {
            "error": "Forbidden",
            "status_code": 403,
            "message": message,
        },
        status=403,
    )


def handler404(request, exception=None):
    """Handle 404 Not Found errors with JSON response."""
    message = "The requested resource was not found."
    if exception:
        message = str(exception) if str(exception) else message
    
    return JsonResponse(
        {
            "error": "Not Found",
            "status_code": 404,
            "message": message,
            "path": request.path,
        },
        status=404,
    )


def handler500(request):
    """Handle 500 Internal Server Error with JSON response."""
    logger.error("Server Error (500)", exc_info=True, extra={"request": request})
    return JsonResponse(
        {
            "error": "Internal Server Error",
            "status_code": 500,
            "message": "An error occurred while processing your request. Please try again later.",
        },
        status=500,
    )
