FROM grafana/grafana:latest
ADD ./provisioning /etc/grafana/provisioning
ADD ./config.ini /etc/grafana/config.ini
RUN  grafana-cli plugins install simpod-json-datasource