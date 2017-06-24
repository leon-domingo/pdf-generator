FROM leondomingo/ubuntu16.04-python3.6.1
LABEL name "pdf-generator"
ENV UPDATED=20170624_1800

# switch "sh" and "bash"
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# update repositories
RUN apt-get update -y

# instalar wkhtmltopdf (/wkhtmltox/bin/wkhtmltopdf)
RUN apt-get install -y libxrender1 libfontconfig1 libxext6
WORKDIR /
RUN wget -q "https://downloads.wkhtmltopdf.org/0.12/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz"
RUN tar xJf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
RUN rm wkhtmltox-0.12.4_linux-generic-amd64.tar.xz

# copiar aplicación Flask (Python)
RUN mkdir app
WORKDIR /app
COPY . .
COPY ./docker/config-docker.py pdf_generator/config.py

# instalar "requirements" de la aplicación
RUN pip install -r requirements.txt

# instalar "gunicorn"
RUN pip install gunicorn
RUN ln -s /opt/python3.6/bin/gunicorn /usr/bin/gunicorn

# instalar "MongoDB 3.4"
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
RUN echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.4.list
RUN apt-get update
RUN apt-get install -y mongodb-org

# instalar "supervisor" (con Python 2.7)
RUN /opt/python3.6/bin/virtualenv -p python2 /superv
RUN /superv/bin/pip install supervisor
RUN ln -s /superv/bin/supervisord /usr/bin/supervisord
RUN ln -s /superv/bin/echo_supervisord_conf /usr/bin/echo_supervisord_conf

# configurar "supervisor"
RUN echo_supervisord_conf > /etc/supervisord.conf
COPY ./docker/supervisord.conf /supervisord.conf
RUN cat /supervisord.conf >> /etc/supervisord.conf
RUN mkdir /var/log/pdf-generator
RUN mkdir /python_eggs
COPY ./docker/supervisord /etc/init.d/
RUN update-rc.d -f supervisord defaults

# arrancar aplicación
EXPOSE 8000
COPY ./docker/run.sh /run.sh
RUN chmod u+x /run.sh
CMD ["/run.sh"]
