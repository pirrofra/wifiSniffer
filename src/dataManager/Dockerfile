FROM python:alpine3.7
COPY . /wifiSniffer/dataManager
WORKDIR /wifiSniffer/dataManager
RUN pip install -r requirements.txt
ENTRYPOINT [ "python" ]
CMD ["dataManager.py"]
