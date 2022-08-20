#!/usr/bin/env python3

import argparse
from time import sleep
from prometheus_client import start_http_server, Summary,Gauge
import board
import busio
import adafruit_bmp3xx

i2c = board.I2C()
bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c,0x76)


bmp.pressure_oversampling = 8
bmp.temperature_oversampling = 2


parser = argparse.ArgumentParser(description="Prometheus exporter for bmp390 air quality sensor")
parser.add_argument('--listen', action='store', default='0.0.0.0', help='bind to address, default: 0.0.0.0')
parser.add_argument('--port', action='store', type=int, default=8001, help='bind to port, default: 8002')
parser.add_argument('--polling_interval', action='store', type=int, default=3, help='sensor polling interval, seconds, default: 1')
parser.add_argument('--verbose', action="store_true", help='print every poll result to stdout')

args = parser.parse_args()


temp = Gauge('bmp390_temp', 'temp level, ppm')
pressure = Gauge('bmp390_pressure', 'Total Volatile Organic Compounds level, ppm')

def get_data():
    #print("temp: ", ccs.getetemp(), "ppm, pressure: ", ccs.getpressure(), " temp: ", temp)
    bmp390_temp = bmp.temperature
    bmp390_pressure = bmp.pressure
    temp_value=bmp390_temp
    pressure_value=bmp390_pressure
    temp.set(temp_value)
    pressure.set(pressure_value)
    if args.verbose:
        print("temp = %d C \t pressure = %d hPa" % (temp, pressure))

if __name__ == '__main__':
    start_http_server(args.port, args.listen)
    while True:
        get_data()
        sleep(args.polling_interval)
