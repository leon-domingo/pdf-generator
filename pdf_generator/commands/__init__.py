# coding=utf8

from flask.ext.script import Command, Option
from ..lib import PdfGenerator


class ScheduleCmd(Command):
    """
    Planifica (reparte) las tareas entre los procesos siguiendo una política round-robin, y teniendo en cuenta la prioridad
    de las tareas y los procesos (PDF_GENERATOR_PROCESOS).
    """

    def run(self):
        pg = PdfGenerator()
        pg.schedule()


class ProcesarCmd(Command):
    """Procesa las tareas pendientes"""

    option_list = (
        Option('--proceso', '-p', dest='proceso', default=1),
    )

    def run(self, proceso):
        pg = PdfGenerator()
        pg.process(proceso)


class CleanCmd(Command):
    """Limpiar tareas ya realizadas"""

    option_list = (
        Option('--age', '-a', dest='age', default=None),
    )

    def run(self, age):
        pg = PdfGenerator()
        age = int(age) if age is not None else None
        pg.clean(age)
