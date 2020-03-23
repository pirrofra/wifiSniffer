FROM python:alpine3.7
COPY . /wifiSniffer/dataAnalysis
WORKDIR /wifiSniffer/dataAnalysis
RUN pip install -r requirements.txt
ENV FLASK_APP dataAnalysis.py
CMD [ "gunicorn","-b 1000","dataAnalysis:app" ]