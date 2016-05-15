#!/bin/bash
SCRIPT_PATH=`dirname $0`
$SCRIPT_PATH/venv/bin/python $SCRIPT_PATH/manage.py runserver -p 5550
