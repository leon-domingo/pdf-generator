# coding=utf8

from flask import Flask
from flask_pymongo import PyMongo
from .config import Config
import logging
import sys
import time
from pymongo.errors import ConnectionFailure

mongo = PyMongo()


def create_app():
    """Factory app creator."""

    app = Flask(__name__, static_url_path='', static_folder='static')

    # settings
    app.config.from_object(Config)

    # set up logging
    lh  = logging.StreamHandler(sys.stderr)
    fmt = logging.Formatter(Config.LOG_FORMAT)
    lh.setFormatter(fmt)

    app.logger.setLevel(Config.LOG_LEVEL)
    app.logger.handlers = [lh]

    # set up MongoDB
    conectado = False
    intentos  = 0
    db_conn_retries = Config.get('DB_CONN_RETRIES', 5)
    db_conn_wait    = Config.get('DB_CONN_WAIT', 60)
    while not conectado:
        try:
            app.logger.debug('Conectando a MongoDB...({0} {1})'.format(db_conn_retries - intentos, Config.get('MONGO_DBNAME')))
            intentos += 1
            mongo.init_app(app)
            conectado = True

        except ConnectionFailure:
            conectado = False
            app.logger.warn('Error de conexión. Esperando {0} segundos...'.format(db_conn_wait))
            time.sleep(db_conn_wait)

            if intentos == db_conn_retries:
                app.logger.error(u'Se ha superado el nº de intentos de conexión ({0})'.format(db_conn_retries))
                raise

    # set up apps (routes)
    for app_module in Config.APPS:
        if isinstance(app_module, str):
            # 'foo.bar'
            app.logger.debug(u'Setting up route "{}"'.format(app_module))
            m = __import__(app_module, fromlist=['init_routes'])

            m.init_routes(app)

        elif hasattr(app_module, '__iter__'):
            # list, tuple
            # ('foo.bar.BazRoute', '/')
            path, route_base = app_module
            module_name = '.'.join(path.split('.')[:-1])
            cls_name = path.split('.')[-1]

            app.logger.debug(u'Setting up route "{}" on "{}"'.format(path, route_base))
            m = __import__(module_name, fromlist=[cls_name])

            cls = getattr(m, cls_name)
            cls.register(app, route_base=route_base)

    return app
