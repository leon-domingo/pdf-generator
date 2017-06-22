# coding=utf8

from flask import request
from flask_classy import FlaskView, route
from ..config import Config
from ..lib import PdfGenerator

from ..lib.util import (template_or_json,
                        _error)


class PdfGeneratorRoute(FlaskView):

    route_prefix = ''

    # /to-pdf
    @route('/to-pdf', methods=['POST'])
    @template_or_json()
    def to_pdf(self):
        """
        IN
            {
                "headers": [["name", "value"], ...],
                "cookies": [["name", "value"], ...],
                "margins": [10, 10, 10, 10],
                "size: "A3"
                "viewport-size": "1200x1200"
                "url": "...",
                "attachments": ["...", ...]
            }

        OUT
            status <bool> --> True=éxito, False=fallo
            pdf    <str>  --> Contenido del PDF en Base64
        """

        try:
            pg = PdfGenerator()
            # id_tarea = pg.register(request.get_json())
            datos = pg.resolve(request.get_json())

            return {'status': True, 'pdf': datos['pdf']}

        except Exception as e:
            _error(e)
            return {'status': False}

    @route('/status', methods=['GET'])
    @template_or_json()
    def status(self):
        try:
            return {
                'status': True,
                'config': {
                    'wkhtmltopdf_path': Config.WKHTMLTOPDF_PATH,
                    'mongodb': {
                        'dbname': Config.MONGO_DBNAME,
                        'host': Config.MONGO_HOST,
                    },
                    'commands': [f'{c[0]}.{c[1]}::{c[2]}' for c in Config.COMMANDS],
                }
            }

        except Exception as e:
            _error(e)
            return {'status': False}
