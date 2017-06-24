# coding=utf8

from flask import request
from flask_classy import FlaskView, route
import pytz
import datetime as dt
import pymongo
from .. import mongo
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
            # obtener tareas pendientes de limpieza
            max_age = Config.get('PDF_GENERATOR_MAX_AGE', 12 * 3600)
            limit = dt.datetime.now(pytz.utc) - dt.timedelta(seconds=max_age)

            qry = {
                'completado': {'$lt': limit},
                'limpio': None
            }

            num_tareas = mongo.db.tareas.count()
            num_tareas_pendientes_limpieza = mongo.db.tareas.count(qry)

            # en proceso
            qry_en_proceso = {
                'completado': None,
                'en_proceso': True,
            }
            num_tareas_en_proceso = mongo.db.tareas.count(qry_en_proceso)

            # no completadas
            qry_no_completadas = {
                'completado': None,
            }
            num_tareas_no_completadas = mongo.db.tareas.count(qry_no_completadas)

            # pendientes
            qry_pendientes = {
                'completado': None,
                'proceso': {'$ne': None},
            }
            num_tareas_pendientes = mongo.db.tareas.count(qry_pendientes)

            # timezone
            tz = request.args.get('tz', Config.get('PDF_GENERATOR_TIMEZONE', 'Europe/Madrid'))

            ahora = dt.datetime.now(pytz.utc)

            # última tarea REGISTRADA
            ultima_tarea_registrada = mongo.db.tareas.find({})\
                .sort([('registrado', pymongo.DESCENDING)])\
                .limit(1)

            ultima_tarea_registrada_ = {}
            if ultima_tarea_registrada.count() > 0:

                t = ultima_tarea_registrada[0]

                ultima_tarea_registrada_ = {
                    'timestamp': t['registrado'].astimezone(pytz.timezone(tz)).isoformat(),
                    'elapsed_s': (ahora - t['registrado']).seconds,
                    'elapsed_h': round((ahora - t['registrado']).seconds / 3600, 2),
                }

            # última tareas COMPLETADA
            ultima_tarea_completada = mongo.db.tareas.find({'completado': {'$ne': None}})\
                .sort([('completado', pymongo.DESCENDING)])\
                .limit(1)

            ultima_tarea_completada_ = {}
            if ultima_tarea_completada.count() > 0:

                tarea = ultima_tarea_completada[0]

                ultima_tarea_completada_ = {
                    'timestamp': tarea['completado'].astimezone(pytz.timezone(tz)).isoformat(),
                    'elapsed_s': (ahora - tarea['completado']).seconds,
                    'elapsed_h': round((ahora - tarea['completado']).seconds / 3600, 2),
                }

            # comprobar "limpieza"
            ultima_limpieza = mongo.db.limpiezas.find({})\
                .sort([('timestamp', pymongo.DESCENDING)])\
                .limit(1)

            limpieza_done = False

            if ultima_limpieza.count() > 0:
                limpieza = ultima_limpieza[0]

                max_age = Config.get('PDF_GENERATOR_MAX_AGE', 12 * 3600)
                diff = (ahora - limpieza['timestamp']).seconds
                if diff > max_age:
                    # TODO: ejecutar "clean"
                    pg = PdfGenerator()
                    pg.clean()

                    limpieza_done = True

            else:
                pg = PdfGenerator()
                pg.clean()

                limpieza_done = True

            return {
                'status': True,
                # 'config': {
                #     'wkhtmltopdf_path': Config.WKHTMLTOPDF_PATH,
                #     'mongodb': {
                #         'dbname': Config.MONGO_DBNAME,
                #         'host': Config.MONGO_HOST,
                #     },
                #     'commands': [f'{c[0]}.{c[1]}::{c[2]}' for c in Config.COMMANDS],
                # },
                'data': {
                    'tareas_totales': num_tareas,
                    'tareas_pendientes_limpieza': num_tareas_pendientes_limpieza,
                    'tareas_no_completadas': num_tareas_no_completadas,
                    'tareas_pendientes': num_tareas_pendientes,
                    'tareas_en_proceso': num_tareas_en_proceso,
                    'tz': tz,
                    'ultima_tarea_registrada': ultima_tarea_registrada_,
                    'ultima_tarea_completada': ultima_tarea_completada_,
                    'limpieza': limpieza_done,
                }
            }

        except Exception as e:
            _error(e)
            return {'status': False}

    @route('/clean', methods=['GET'])
    @template_or_json()
    def clean(self):
        try:
            num_tareas = mongo.db.tareas.count()

            pg = PdfGenerator()
            limpiezas_totales, limpiezas_realizadas = pg.clean()

            return {
                'status': True,
                'data': {
                    'tareas_totales': num_tareas,
                    'limpiezas_totales': limpiezas_totales,
                    'limpiezas_realizadas': limpiezas_realizadas,
                }
            }

        except Exception as e:
            _error(e)
            return {'status': False}
