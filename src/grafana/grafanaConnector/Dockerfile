FROM python:alpine3.7
COPY . /wifiSniffer/grafanaConnector
WORKDIR /wifiSniffer/grafanaConnector
RUN pip install -r requirements.txt
ENV FLASK_APP grafanaConnector.py
CMD gunicorn --timeout 1000 -b 0.0.0.0:5000 grafanaConnector:app
