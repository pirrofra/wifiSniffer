FROM python:alpine3.7
COPY . /wifiSniffer/grafanaConnector
WORKDIR /wifiSniffer/grafanaConnector
RUN pip install -r requirements.txt
ENV FLASK_APP grafanaConnector.py
CMD [ "gunicorn","-b 0.0.0.0:5000","grafanaConnector:app" ]
