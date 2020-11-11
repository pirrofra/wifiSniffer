FROM python:alpine3.7
COPY . /wifiSniffer/dataInjector
WORKDIR /wifiSniffer/dataInjector
RUN pip install -r requirements.txt
ENV FLASK_APP dataInjector.py
CMD gunicorn --timeout 1000 -b 0.0.0.0:5000 dataInjector:app