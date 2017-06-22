#!/bin/bash

# inicializar ficheros
touch /var/log/pdf-generator/ws_out.log
touch /var/log/pdf-generator/ws_err.log
touch /var/log/pdf-generator/schedule_out.log
touch /var/log/pdf-generator/schedule_err.log
touch /var/log/pdf-generator/procesar-1_out.log
touch /var/log/pdf-generator/procesar-1_err.log
touch /var/log/pdf-generator/procesar-2_out.log
touch /var/log/pdf-generator/procesar-2_err.log
touch /var/log/pdf-generator/procesar-3_out.log
touch /var/log/pdf-generator/procesar-3_err.log
touch /var/log/pdf-generator/procesar-4_out.log
touch /var/log/pdf-generator/procesar-4_err.log
touch /var/log/pdf-generator/mongodb_out.log
touch /var/log/pdf-generator/mongodb_err.log

/etc/init.d/supervisord restart && \
    tail -f -q \
        /var/log/pdf-generator/ws_out.log \
        /var/log/pdf-generator/ws_err.log \
        /var/log/pdf-generator/schedule_out.log \
        /var/log/pdf-generator/schedule_err.log \
        /var/log/pdf-generator/procesar-1_out.log \
        /var/log/pdf-generator/procesar-1_err.log \
        /var/log/pdf-generator/procesar-2_out.log \
        /var/log/pdf-generator/procesar-2_err.log \
        /var/log/pdf-generator/procesar-3_out.log \
        /var/log/pdf-generator/procesar-3_err.log \
        /var/log/pdf-generator/procesar-4_out.log \
        /var/log/pdf-generator/procesar-4_err.log \
        /var/log/pdf-generator/mongodb_out.log \
        /var/log/pdf-generator/mongodb_err.log
