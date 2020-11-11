FROM python:alpine3.7
COPY . /wifiSniffer/dataManager
WORKDIR /wifiSniffer/dataManager
RUN pip install -r requirements.txt
ENV FLASK_APP dataManager.py
CMD gunicorn --timeout 1000 -b 0.0.0.0:5000 dataManager:app
