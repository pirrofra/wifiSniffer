FROM python:alpine3.7
COPY . /wifiSniffer/dataCleaner
WORKDIR /wifiSniffer/dataCleaner
RUN pip install -r requirements.txt
ENV FLASK_APP dataCleaner.py
CMD [ "flask","run","--host 0.0.0.0","--port 1000" ]
