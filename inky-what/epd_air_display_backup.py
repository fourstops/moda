#!/usr/bin/env python3

import sys
import os

import aqi
from prometheus_api_client import PrometheusConnect,  MetricSnapshotDataFrame
from PIL import Image, ImageDraw, ImageFont
from inky.inky_uc8159 import Inky

from font_source_serif_pro import SourceSerifProSemibold
from font_source_sans_pro import SourceSansProSemibold

prom = PrometheusConnect(url ='http://192.168.0.223:9090', disable_ssl=True)
PATH = os.path.dirname(__file__)

deck_label_config = {'location': 'deck'}
living_label_config = {'location': 'living_room'}

pm1_data = prom.get_current_metric_value(
    metric_name='PM1',
    label_config=deck_label_config,
)

pm25_data = prom.get_current_metric_value(
    metric_name='PM25',
    label_config=deck_label_config,
)

pm10_data = prom.get_current_metric_value(
    metric_name='PM10',
    label_config=deck_label_config,
)

co2_data = prom.get_current_metric_value(
    metric_name='sgp30_eco2',
    label_config=living_label_config,
    )

voc_data = prom.get_current_metric_value(
    metric_name='sgp30_tvoc',
    label_config=living_label_config,
    )

in_data = prom.get_current_metric_value(
    metric_name='temperature',
    label_config=living_label_config,
    )

out_data = prom.get_current_metric_value(
    metric_name='temperature',
    label_config=deck_label_config,
    )

df_pm1 = MetricSnapshotDataFrame(pm1_data)
df_pm25 = MetricSnapshotDataFrame(pm25_data)
df_pm10 = MetricSnapshotDataFrame(pm10_data)
df_co2 = MetricSnapshotDataFrame(co2_data)
df_voc = MetricSnapshotDataFrame(voc_data)
df_in = MetricSnapshotDataFrame(in_data)
df_out = MetricSnapshotDataFrame(out_data)

p_pm1 = df_pm1.head()
p_pm25 = df_pm25.head()
p_pm10 = df_pm10.head()
p_co2 = df_co2.head()
p_voc = df_voc.head()
p_in = df_in.head()
p_out = df_out.head()

pm1 = p_pm1['value'].to_string(index=False)
pm25 = p_pm25['value'].to_string(index=False)
pm10 = p_pm10['value'].to_string(index=False)
co2 = p_co2['value'].to_string(index=False)
voc = p_voc['value'].to_string(index=False)
t_in = p_in['value'].to_string(index=False)
t_out = p_out['value'].to_string(index=False)

tf_in = "{:.1f}".format(float(t_in) * 1.8 + 32)
tf_out = "{:.1f}".format(float(t_out) * 1.8 + 32)

myaqi = aqi.to_aqi([
    (aqi.POLLUTANT_PM25, pm25),
    (aqi.POLLUTANT_PM10, pm10),
], algo=aqi.ALGO_EPA)

inky_display = Inky()
saturation = 1.0

img = Image.open(os.path.join(PATH, "resources/bluegreentable.png"))
draw = ImageDraw.Draw(img)

metric_font_size = 74
value_font_size = 74

metric_font = ImageFont.truetype(SourceSerifProSemibold, metric_font_size)
value_font = ImageFont.truetype(SourceSansProSemibold, value_font_size)

draw.text((150, 20), str(myaqi), inky_display.BLACK, font=metric_font)
draw.text((150, 120), pm1, font=metric_font)
draw.text((150, 230), pm25, font=metric_font)
draw.text((150, 330), pm10, inky_display.BLACK, font=metric_font)

draw.text((375, 20), co2, font=metric_font)
draw.text((375, 120), voc, inky_display.BLACK, font=metric_font)
draw.text((375, 230), tf_in, font=metric_font)
draw.text((375, 330), tf_out, font=metric_font)


inky_display.set_image(img, saturation=saturation)
inky_display.show()
