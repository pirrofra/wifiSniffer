FROM python:alpine3.7
COPY . /wifiSniffer/dataManager
WORKDIR /wifiSniffer/dataManager
RUN pip install -r requirements.txt
ENV FLASK_APP dataManager.py
CMD [ "gunicorn","-b 0.0.0.0:5000","dataManager:app" ]
