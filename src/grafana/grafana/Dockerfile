FROM grafana/grafana:7.3.1
ADD ./provisioning /etc/grafana/provisioning
ADD ./config.ini /etc/grafana/config.ini
RUN  grafana-cli plugins install simpod-json-datasource 0.2.1
