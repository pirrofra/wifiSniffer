FROM python:alpine3.7
COPY . /wifiSniffer/dataManager
WORKDIR /wifiSniffer/dataManager
RUN pip install -r requirements.txt
ENV FLASK_APP dataManager.py
CMD [ "flask","run","--host 0.0.0.0","--port 1000" ]
