FROM python:alpine3.7
COPY . /wifiSniffer/grafanaRequest
WORKDIR /wifiSniffer/grafanaRequest
RUN pip install -r requirements.txt
ENV FLASK_APP grafanaRequest.py
CMD [ "gunicorn","-b 0.0.0.0:5003","grafanaRequest:app" ]
