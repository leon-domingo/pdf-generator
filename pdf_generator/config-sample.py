# coding=utf8

import logging
import os


class BaseConfig(object):

    @classmethod
    def get(cls, attr_name, default=None):
        return getattr(cls, attr_name, default)

    DEBUG = os.environ.get('PDF_GENERATOR_TEST', '1') == '1'

    # logging settings
    LOG_LEVEL  = logging.DEBUG
    LOG_FORMAT = '{0} %(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s'.format(os.environ.get('PDF_GENERATOR_WORKER_NAME') or '*')
    # para usar con Docker
    # LOG_PATH   = '/var/log/app/{}'.format(os.environ.get('LOG_FILE', 'app.log'))

    MONGO_DBNAME = os.environ.get('PDF_GENERATOR_DBNAME') or 'pdf-generator'
    MONGO_HOST   = os.environ.get('MONGODB_PORT_27017_TCP_ADDR') or 'localhost'
    # MONGO_URI    =
    # MONGO_PORT   = 27017
    # MONGO_USERNAME =
    # MONGO_PASSWORD =

    DB_CONN_WAIT    = 20
    DB_CONN_RETRIES = 3

    # wkhtmltopdf
    WKHTMLTOPDF_PATH = '/home/leon/app/bin/wkhtmltopdf'

    # default timezone
    PDF_GENERATOR_TIMEZONE = 'Europe/Madrid'

    PDF_GENERATOR_DEFAULT_PRIORITY = int(os.environ.get('PDF_GENERATOR_DEFAULT_PRIORITY', 10))

    PDF_GENERATOR_PROCESOS = [
        PDF_GENERATOR_DEFAULT_PRIORITY,
        PDF_GENERATOR_DEFAULT_PRIORITY,
        PDF_GENERATOR_DEFAULT_PRIORITY,
        PDF_GENERATOR_DEFAULT_PRIORITY
    ]

    PDF_GENERATOR_MAX_INTENTOS = 3

    # en segundos
    PDF_GENERATOR_MAX_AGE = 12 * 3600

    # en segundos
    PDF_GENERATOR_TIMEOUT = 30

    APPS = [
        # 'pdf_generator.routes',
        # (path.class_name, route_base)
        ('pdf_generator.routes.PdfGeneratorRoute', '/'),
    ]

    COMMANDS = [
        ('pdf_generator.commands', 'ScheduleCmd', 'schedule'),
        ('pdf_generator.commands', 'ProcesarCmd', 'procesar'),
        ('pdf_generator.commands', 'CleanCmd', 'clean'),
    ]


class ConfigStd(BaseConfig):
    MONGO_DBNAME = 'pdf-generator'


class ConfigTest(BaseConfig):
    MONGO_DBNAME = 'pdf-generator_test'


Config = ConfigStd
if os.environ.get('PDF_GENERATOR_CONFIG') == 'TEST':
    Config = ConfigTest
