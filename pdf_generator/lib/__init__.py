# coding=utf8

import pymongo
import datetime as dt
import pytz
import time
import random
import base64
import tempfile
import subprocess as sp
from io import BytesIO
from PyPDF2 import PdfFileReader, PdfFileWriter
from pdf_generator import mongo
from pdf_generator.config import Config
from .util import _debug, _info, _error  # Timeout


class PdfGenerator(object):

    def __init__(self, *args):
        self.args = args

    def register(self, datos, prioridad=Config.get('PDF_GENERATOR_DEFAULT_PRIORITY', 10)):
        """Registrar una nueva tarea para procesar un alta, indicando prioridad de ejecución opcionalmente."""
        tarea = mongo.db.tareas\
            .insert_one({'datos': datos,
                         'intentos': 0,
                         'registrado': dt.datetime.now(pytz.utc),
                         'prioridad': prioridad,
                         'completado': None,
                         'en_proceso': False})

        return tarea.inserted_id

    def schedule(self):
        """Asignarle a cada tarea el proceso que la va a ejecutar."""
        p_actual = 0
        qry = {'completado': None, 'en_proceso': False, 'proceso': None}
        while True:
            _info(u'Planificando tareas para {} proceso/s'.format(len(Config.PDF_GENERATOR_PROCESOS)))
            for tarea in mongo.db.tareas.find(qry)\
                    .sort([('prioridad', pymongo.ASCENDING), ('registrado', pymongo.ASCENDING)]):

                fin  = False
                paso = 1
                while not fin:
                    p_actual += 1
                    if tarea['prioridad'] >= Config.PDF_GENERATOR_PROCESOS[p_actual - 1] or paso > 1:
                        _info(u'> Asignando proceso {} a tarea {}'.format(p_actual, tarea['_id']))
                        mongo.db.tareas.update_one({'_id': tarea['_id']}, {'$set': {'proceso': p_actual}})
                        fin = True

                    if p_actual == len(Config.PDF_GENERATOR_PROCESOS):
                        p_actual = 0
                        paso += 1

            time.sleep(random.randint(1, 2))

    def clean(self, age=None):
        """
        Limpiar el campo "datos.pdf" para tareas ya procesadas.

        IN
            age <int> (en segundos)

        OUT
            (<int>, <int>)
        """

        # limpiar las tareas con más de X horas de antiguedad (por defecto 12h)
        ahora = dt.datetime.now(pytz.utc)
        max_age = age or Config.get('PDF_GENERATOR_MAX_AGE', 12 * 3600)
        limit = ahora - dt.timedelta(seconds=max_age)
        qry = {
            '$or': [
                {'completado': {'$lt': limit}, 'limpio': None},
                {'registrado': {'$lt': limit}, 'completado': None, 'limpio': None},
            ]
        }
        n = 0
        n0 = mongo.db.tareas.count(qry)
        for tarea in mongo.db.tareas.find(qry):
            try:
                _info('Limpiando tarea "{}"...'.format(tarea['_id']))
                mongo.db.tareas.update_one({'_id': tarea['_id']},
                                           {'$set': {'datos.pdf': '',
                                                     'datos.attachments': [],
                                                     'limpio': ahora,
                                                     'completado': ahora,
                                                     }})

                n += 1

            except Exception as e:
                _error(e)

        mongo.db.limpiezas.insert_one({'timestamp': ahora, 'totales': n0, 'realizadas': n})

        return (n0, n)

    def process(self, proceso):

        # qry = dict(proceso=int(proceso), completado=None, intentos={'$lt': Config.get('PDF_GENERATOR_MAX_INTENTOS', 3)})

        qry = {
            'proceso': int(proceso),
            'completado': None,
            'intentos': {'$lt': Config.get('PDF_GENERATOR_MAX_INTENTOS', 3)},
        }

        while True:
            _info(f'[PROCESO {proceso}: Buscando tareas pendientes...]')
            for tarea in mongo.db.tareas\
                    .find(qry)\
                    .sort([('prioridad', pymongo.ASCENDING), ('registrado', pymongo.ASCENDING)])\
                    .limit(1):

                try:
                    _info(u'Procesando tarea: [{} (registrada el {})]'.format(tarea['_id'], tarea.get('registrado')))

                    # marcar como "en_proceso"
                    # mongo.db.tareas.update(dict(_id=tarea['_id']), {'$set': dict(en_proceso=True)})
                    mongo.db.tareas.update_one({'_id': tarea['_id']}, {'$set': {'en_proceso': True}})

                    data = tarea['datos']
                    _debug(data)

                    # ~/app/bin/wkhtmltopdf --custom-header Authorization pakoporraxeselmejor -q \
                    # -s A3 --margin-top 3 --margin-right 3 --margin-bottom 3 --margin-left 3 \
                    # "http://localhost/mantelroom/wp-admin/admin-ajax.php?action=mrtol__presupuesto_pdf&id=648" ~/Downloads/test.pdf

                    params = [Config.WKHTMLTOPDF_PATH]

                    # --custom-header
                    for (h_name, h_value) in data.get('headers', []):
                        params.extend(['--custom-header', h_name, h_value])

                    # --cookie name value
                    for (ck_name, ck_value) in data.get('cookies', []):
                        params.extend(['--cookie', ck_name, ck_value])

                    # quiet
                    params.append('-q')

                    # size
                    size = data.get('size', 'A3')
                    params.extend(['-s', size])

                    # margins
                    margins = data.get('margins')
                    if margins:
                        (m_top, m_right, m_bottom, m_left) = margins

                        params.extend(['--margin-top', str(m_top)])
                        params.extend(['--margin-right', str(m_right)])
                        params.extend(['--margin-bottom', str(m_bottom)])
                        params.extend(['--margin-left', str(m_left)])

                    # viewport-size
                    viewport_size = data.get('viewport-size')
                    if viewport_size:
                        params.extend(['--viewport-size', viewport_size])

                    # url
                    params.append(data.get('url'))

                    # fichero temporal para salida
                    with tempfile.NamedTemporaryFile(prefix='pdf_generator_', suffix='.pdf') as fichero_pdf:

                        # indicar fichero de salida
                        params.append(fichero_pdf.name)

                        _debug(params)

                        _debug(u'Generando PDF {}'.format(fichero_pdf.name))
                        # sp.check_call(params)
                        sp.call(params)

                        r = BytesIO()

                        # añadir "attachments" al PDF, si los hay
                        attachments = data.get('attachments')
                        if attachments:
                            # añadir 1ª página de la factura
                            pr = PdfFileReader(fichero_pdf)
                            pw = PdfFileWriter()
                            pw.addPage(pr.getPage(0))

                            # añadir "adjuntos"
                            for adjunto in attachments:
                                s = BytesIO()
                                # decodificar adjunto (Base64)
                                s.write(base64.b64decode(adjunto))
                                s.seek(0)
                                pr = PdfFileReader(s)

                                # recorrer páginas del adjunto
                                for p in range(pr.getNumPages()):
                                    pw.addPage(pr.getPage(p))

                            # escribir PDF resultado
                            r_sin_codificar = BytesIO()
                            pw.write(r_sin_codificar)

                            r_sin_codificar.seek(0)
                            r.write(base64.b64encode(r_sin_codificar.read()))

                        else:
                            fichero_pdf.seek(0)
                            r.write(base64.b64encode(fichero_pdf.read()))

                        # actualizar tarea
                        _info(u'Actualizando tarea {}'.format(tarea['_id']))
                        r.seek(0)
                        mongo.db.tareas.update_one({'_id': tarea['_id']},
                                                   {'$set': {'completado': dt.datetime.now(pytz.utc),
                                                             'en_proceso': False,
                                                             'datos.pdf': r.read().decode('utf8'),
                                                             }})

                except Exception as e:
                    # import traceback
                    # traceback.print_exc()

                    _error(e)
                    datos_update = {'en_proceso': False, 'intentos': tarea.get('intentos', 0) + 1}
                    mongo.db.tareas.update_one({'_id': tarea['_id']}, {'$set': datos_update})

            time.sleep(random.randint(1, 2))

    def resolve(self, data):
        id_tarea = self.register(data)
        max_intentos = 10
        intentos = 0
        while True:
            tarea = mongo.db.tareas.find_one({'_id': id_tarea, 'completado': {'$ne': None}})
            if tarea is not None:
                break

            else:
                tarea = mongo.db.tareas.find_one({'_id': id_tarea, 'intentos': Config.PDF_GENERATOR_MAX_INTENTOS})
                if tarea is not None:
                    raise Exception('Se ha alcanzado el nº máximo de intentos')

            time.sleep(2)
            intentos += 1
            if intentos == max_intentos:
                raise Exception('Se ha alcanzado el nº máximo de intentos')

        return tarea['datos']
