#!/usr/bin/env python3

import argparse
from time import sleep
from prometheus_client import start_http_server, Summary,Gauge
import board
import busio
import adafruit_sgp30

i2c_bus = busio.I2C(board.SCL, board.SDA, frequency=100000)
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c_bus)

sgp30.iaq_init()
sgp30.set_iaq_baseline(0x8973, 0x8AAE)

elapsed_sec = 0

parser = argparse.ArgumentParser(description="Prometheus exporter for sgp30 air quality sensor")
parser.add_argument('--listen', action='store', default='0.0.0.0', help='bind to address, default: 0.0.0.0')
parser.add_argument('--port', action='store', type=int, default=8000, help='bind to port, default: 8002')
parser.add_argument('--polling_interval', action='store', type=int, default=3, help='sensor polling interval, seconds, default: 1')
parser.add_argument('--verbose', action="store_true", help='print every poll result to stdout')

args = parser.parse_args()


co2 = Gauge('sgp30_eco2', 'CO2 level, ppm')
tvoc = Gauge('sgp30_tvoc', 'Total Volatile Organic Compounds level, ppm')

def get_data():
    #print("CO2: ", ccs.geteCO2(), "ppm, TVOC: ", ccs.getTVOC(), " temp: ", temp)
    eCO2, TVOC = sgp30.iaq_measure()
    co2_value=eCO2
    tvoc_value=TVOC
    co2.set(co2_value)
    tvoc.set(tvoc_value)
    if args.verbose:
        print("eCO2 = %d ppm \t TVOC = %d ppb" % (eCO2, TVOC))

if __name__ == '__main__':
    start_http_server(args.port, args.listen)
    while True:
        get_data()
        sleep(args.polling_interval)
