FROM python:alpine3.7
COPY . /wifiSniffer/dataCollector
WORKDIR /wifiSniffer/dataCollector
RUN pip install -r requirements.txt
CMD ["python","dataCollector.py"]