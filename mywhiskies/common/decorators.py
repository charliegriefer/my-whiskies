from functools import wraps

from flask import abort
from flask_login import current_user


def validate_username(func):
    @wraps(func)
    def wrapper(username, *args, **kwargs):
        if current_user.username.lower() != username.lower():
            abort(403)
        return func(username, *args, **kwargs)

    return wrapper
