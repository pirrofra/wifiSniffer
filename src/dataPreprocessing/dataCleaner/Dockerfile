FROM python:alpine3.7
COPY . /wifiSniffer/dataCleaner
WORKDIR /wifiSniffer/dataCleaner
RUN pip install -r requirements.txt
CMD [ "python","dataCleaner.py" ]
