import os
from flask import request, abort
from .backend_utils import db as db_utils
from functools import wraps

STATIC_TOKEN = os.environ.get("AI_SEARCH_STATIC_BEARER_TOKEN")

def token_required(f):
    """
    Decorator to validate the static bearer token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check if the 'Authorization' header is present
        if 'Authorization' in request.headers:
            # Extract the token part (Bearer <token>)
            auth_header = request.headers['Authorization']
            try:
                # Split the header into "Bearer" and the actual token
                scheme, token = auth_header.split()
                if scheme.lower() != 'bearer':
                    token = None
            except ValueError:
                # Handle cases where the header is not in the "Bearer <token>" format
                error_obj = db_utils.log_error(
                    error_log="Authentication required: Missing or invalid token",
                    error_msg="authentication-required",
                    origin="token_required",
                )
                return error_obj, 401
        

        # If no valid token is found, return an error
        if not token:
            error_obj = db_utils.log_error(
                error_log="Authentication required: Missing or invalid token",
                error_msg="authentication-required",
                origin="token_required",
            )
            return error_obj, 401

        # Validate the token against the static value
        if token != STATIC_TOKEN:
            error_obj = db_utils.log_error(
                error_log="Authentication required: Missing or invalid token",
                error_msg="authentication-required",
                origin="token_required",
            )
            return error_obj, 401

        # Return the result from the wrapper
        return f(*args, **kwargs)

    # The decorator returns the new wrapper function
    return decorated
