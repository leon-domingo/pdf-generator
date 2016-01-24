# -*- coding: utf-8 -*-

import pymongo
import datetime as dt
import pytz
# import os
import time
import random
import base64
import tempfile
import subprocess as sp
# import requests
# from StringIO import StringIO
# from pyPdf import PdfFileReader, PdfFileWriter
from pdf_generator import mongo
from pdf_generator.config import Config
from .util import _debug, _info, _error, Timeout


class PdfGenerator(object):

    def __init__(self, *args):
        self.args = args

    def register(self, datos, prioridad=Config.get('PDF_GENERATOR_DEFAULT_PRIORITY', 10)):
        """Registrar una nueva tarea para procesar un alta, indicando prioridad de ejecución opcionalmente"""

        tarea = mongo.db.tareas.\
            insert_one(dict(datos=datos,
                            intentos=0,
                            registrado=dt.datetime.now(pytz.utc),
                            prioridad=prioridad,
                            completado=None,
                            en_proceso=False))

        return tarea.inserted_id

    def schedule(self):
        """Asignarle a cada tarea el proceso que la va a ejecutar"""

        p_actual = 0
        qry = dict(completado=None, en_proceso=False, proceso=None)
        while True:
            _info(u'Planificando tareas para {} proceso/s'.format(len(Config.PDF_GENERATOR_PROCESOS)))
            for tarea in mongo.db.tareas.find(qry).\
                    sort([['prioridad', pymongo.ASCENDING],
                          ['registrado', pymongo.ASCENDING]]):

                fin  = False
                paso = 1
                while not fin:
                    p_actual += 1
                    if tarea['prioridad'] >= Config.PDF_GENERATOR_PROCESOS[p_actual - 1] or paso > 1:
                        _info(u'> Asignando proceso {} a tarea {}'.format(p_actual, tarea['_id']))
                        mongo.db.tareas.update(dict(_id=tarea['_id']), {'$set': dict(proceso=p_actual)})
                        fin = True

                    if p_actual == len(Config.PDF_GENERATOR_PROCESOS):
                        p_actual = 0
                        paso += 1

            time.sleep(random.randint(1, 2))

    def process(self, proceso):
        qry = dict(proceso=int(proceso), completado=None, intentos={'$lt': Config.get('PDF_GENERATOR_MAX_INTENTOS', 3)})

        while True:
            _info('[PROCESO {}: Buscando tareas pendientes...]'.format(proceso))
            for tarea in mongo.db.tareas.\
                    find(qry).sort([['prioridad', pymongo.ASCENDING],
                                    ['registrado', pymongo.ASCENDING]]).\
                    limit(1):

                try:
                    _info(u'Procesando tarea: [{} (registrada el {})]'.format(tarea['_id'], tarea.get('registrado')))

                    # marcar como "en_proceso"
                    mongo.db.tareas.update(dict(_id=tarea['_id']), {'$set': dict(en_proceso=True)})

                    data = tarea['datos']

                    # ~/app/bin/wkhtmltopdf --custom-header Authorization pakoporraxeselmejor -q \
                    # -s A3 --margin-top 3 --margin-right 3 --margin-bottom 3 --margin-left 3 \
                    # "http://localhost/mantelroom/wp-admin/admin-ajax.php?action=mrtol__presupuesto_pdf&id=648" ~/Downloads/test.pdf

                    params = [Config.WKHTMLTOPDF_PATH]

                    # --custom-header
                    for h in data.get('headers', []):
                        params.append('--custom-header')
                        params.append(h[0])
                        params.append(h[1])

                    # quiet
                    params.append('-q')

                    # size
                    size = data.get('size', 'A3')
                    params.append('-s')
                    params.append(size)

                    # margins
                    margins = data.get('margins')
                    if margins:
                        params.append('--margin-top')
                        params.append(str(margins[0]))

                        params.append('--margin-right')
                        params.append(str(margins[1]))

                        params.append('--margin-bottom')
                        params.append(str(margins[2]))

                        params.append('--margin-left')
                        params.append(str(margins[3]))

                    # url
                    params.append(data.get('url'))

                    # fichero temporal para salida
                    with tempfile.NamedTemporaryFile(prefix='pdf_generator_', suffix='.pdf') as fichero_pdf:

                        # indicar fichero de salida
                        params.append(fichero_pdf.name)

                        _debug(u'Generando PDF {}'.format(fichero_pdf.name))
                        sp.check_call(params)

                        fichero_pdf.seek(0)
                        
                        # actualizar tarea
                        _info(u'Actualizando tarea {}'.format(tarea['_id']))
                        mongo.db.tareas.update(dict(_id=tarea['_id']),
                                               {'$set': {'completado': dt.datetime.now(pytz.utc),
                                                         'en_proceso': False,
                                                         'datos.pdf': base64.b64encode(fichero_pdf.read())
                                                         }})

                except Exception as e:
                    _error(e)
                    datos_update = dict(en_proceso=False, intentos=tarea.get('intentos', 0) + 1)
                    mongo.db.tareas.update(dict(_id=tarea['_id']), {'$set': datos_update})

            time.sleep(random.randint(1, 2))

    def resolve(self, data):
        id_tarea = self.register(data)
        max_intentos = 10
        intentos = 0
        while True:
            tarea = mongo.db.tareas.find_one(dict(_id=id_tarea, completado={'$ne': None}))
            if tarea is not None:
                break

            else:
                tarea = mongo.db.tareas.find_one(dict(_id=id_tarea,
                                                      intentos=Config.PDF_GENERATOR_MAX_INTENTOS))
                if tarea is not None:
                    raise Exception('Se ha alcanzado el nº máximo de intentos')

            time.sleep(2)
            intentos += 1
            if intentos == max_intentos:
                raise Exception('Se ha alcanzado el nº máximo de intentos')

        return tarea['datos']
