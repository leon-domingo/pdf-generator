# -*- coding: utf-8 -*-

from flask import request, current_app
from flask.ext.classy import FlaskView, route
from ..lib import PdfGenerator
from ..lib.util import template_or_json


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
                "url": "...",
                "attachments": ["...", ...]
            }

        OUT
            status    <bool>
            id_tarea  <str>
        """

        try:
            pg = PdfGenerator()
            # id_tarea = pg.register(request.get_json())
            datos = pg.resolve(request.get_json())

            return dict(status=True, pdf=datos['pdf'])

        except Exception as e:
            current_app.logger.error(e)
            return dict(status=False)


def init_routes(app):
    PdfGeneratorRoute.register(app, route_base='/')
