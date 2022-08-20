#!/usr/bin/env python3
import time
import board
import busio
import digitalio
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility
import argparse
from prometheus_client import start_http_server, Summary,Gauge

i2c = busio.I2C(board.SCL, board.SDA)
apds = APDS9960(i2c)
parser = argparse.ArgumentParser(description="Prometheus exporter for sgp30 air quality sensor")
parser.add_argument('--listen', action='store', default='0.0.0.0', help='bind to address, default: 0.0.0.0')
parser.add_argument('--port', action='store', type=int, default=8003, help='bind to port, default: 8002')
parser.add_argument('--polling_interval', action='store', type=int, default=1, help='sensor polling interval, seconds, default: 1')
parser.add_argument('--verbose', action="store_true", help='print every poll result to stdout')

args = parser.parse_args()
apds.enable_color = True

red = Gauge('apds9960_red', 'Red, value')
green = Gauge('apds9960_green', 'Green, value')
blue = Gauge('apds9960_blue', 'Blue, value')
clear = Gauge('apds9960_clear', 'Clear, value')
color_temp = Gauge('apds9960_color_temp', 'Color Temp, kelvin')
lux = Gauge('apds9960_lux', 'Lux, value')

def get_data():
    while not apds.color_data_ready:
        time.sleep(0.005)

    r, g, b, c = apds.color_data
    
    red_value = r
    red.set(red_value)
    green_value = g
    green.set(green_value)
    blue_value = b
    blue.set(blue_value)
    clear_value = c
    clear.set(clear_value)
    
    color_temp_value = colorutility.calculate_color_temperature(r, g, b)
    color_temp.set(color_temp_value)
    lux_value = colorutility.calculate_lux(r, g, b)
    lux.set(lux_value)
    time.sleep(0.5)
    if args.verbose:
        print("r: {}, g: {}, b: {}, c: {}".format(r, g, b, c))

if __name__ == '__main__':
    start_http_server(args.port, args.listen)
    while True:
        get_data()
        time.sleep(args.polling_interval)
