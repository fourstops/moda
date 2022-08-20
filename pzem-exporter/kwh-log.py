#!/usr/bin/env python3

import sys
import os
import logging

from prometheus_api_client import PrometheusConnect,  MetricSnapshotDataFrame

prom = PrometheusConnect(url ='http://192.168.0.103:9090', disable_ssl=True)
PATH = os.path.dirname(__file__)

# energy{group="environment", instance="192.168.0.137:8002", job="environment", location="pzem-016"}

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("kwh.log"),
              logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S')

kwh_label_config = {'location': 'pzem-016'}

kwh_data = prom.get_current_metric_value(
    metric_name='energy',
    label_config=kwh_label_config,
)

df_kwh= MetricSnapshotDataFrame(kwh_data)

p_kwh = df_kwh.head()

kwh = p_kwh['value'].to_string(index=False)

logging.info(kwh)

print(kwh)
