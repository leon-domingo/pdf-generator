# -*- coding: utf-8 -*-

from flask import request, render_template, current_app
from flask.json import jsonify
from functools import wraps
import signal


def _info(msg):
    current_app.logger.info(msg)


def _debug(msg):
    current_app.logger.debug(msg)


def _error(msg):
    current_app.logger.error(msg)


def template_or_json(template=None):
    def decorated(f):
        @wraps(f)
        def decorated_fn(*args, **kwargs):
            ctx = f(*args, **kwargs)
            if request.is_xhr or not template:
                return jsonify(ctx)
                
            else:
                return render_template(template, **ctx)

        return decorated_fn

    return decorated


class TimeoutError(Exception):
    pass


class Timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)
