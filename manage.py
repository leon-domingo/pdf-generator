#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask.ext.script import Manager
from pdf_generator import create_app
from pdf_generator.config import Config

app = create_app()
manager = Manager(app)

# set up commands (Config.COMMANDS)
for module_name, class_name, command in Config.COMMANDS:
    app.logger.debug(u'Setting up command: "{}"'.format(command))
    m = __import__(module_name, fromlist=[class_name])
    
    try:
        manager.add_command(command, getattr(m, class_name)())

    except AttributeError:
        app.logger.warn(u'>>>No "{}" command'.format(command))

if __name__ == '__main__':
    manager.run()
