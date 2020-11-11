FROM python:alpine3.7
COPY . /wifiSniffer/dataAnalysis
WORKDIR /wifiSniffer/dataAnalysis
RUN pip install -r requirements.txt
ENV FLASK_APP dataAnalysis.py
CMD gunicorn --timeout 1000 -b 0.0.0.0:5000 dataAnalysis:app