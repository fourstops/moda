#!/usr/bin/env python3

import board
import argparse
from time import sleep
import adafruit_ccs811
import adafruit_bme680
import adafruit_sgp40
from prometheus_client import start_http_server, Summary,Gauge

parser = argparse.ArgumentParser(description="Prometheus exporter for ccs811 air quality sensor")
parser.add_argument('--bind', action='store', default='0.0.0.0', help='bind to address, default: 0.0.0.0')
parser.add_argument('--port', action='store', type=int, default=8002, help='bind to port, default: 8002')
parser.add_argument('--polling_interval', action='store', type=int, default=2, help='sensor polling interval, seconds, default: 1')
parser.add_argument('--verbose', action="store_true", help='print every poll result to stdout')
args = parser.parse_args()

i2c = board.I2C()  # uses board.SCL and board.SDA
ccs811 = adafruit_ccs811.CCS811(i2c)
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)
sgp40 = adafruit_sgp40.SGP40(i2c)

# Wait for the sensor to be ready
while not ccs811.data_ready:
    pass

#temp = ccs.calculateTemperature()
#ccs.tempOffset = temp - 25.0

co2 = Gauge('ccs811_co2', 'CO2 level, ppm')
tvoc = Gauge('ccs811_tvoc', 'Total Volatile Organic Compounds level, ppm')
temperature = Gauge('bme680_temp', 'Air Temperature, C')
humidity = Gauge('bme680_humidity', 'Relative Humidity %')
voc_index = Gauge('sgp40_voc_index', 'Volatile Organic Compounds Index, int')
compensated_raw_gas = Gauge('sgp40_raw_gas', 'Compensated voc index resistance readings, ohms')

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

@REQUEST_TIME.time()
def get_data():
    co2_value=ccs811.eco2
    tvoc_value=ccs811.tvoc
    temperature_value=bme680.temperature
    humidity_value=bme680.relative_humidity
    voc_index_value=sgp40.measure_index(temperature=temperature_value, relative_humidity=humidity_value)
    compensated_raw_gas_value=sgp40.measure_raw( temperature=temperature_value, relative_humidity=humidity_value)
    
    co2.set(co2_value)
    tvoc.set(tvoc_value)
    temperature.set(temperature_value)
    humidity.set(humidity_value)
    voc_index.set(voc_index_value)
    compensated_raw_gas.set(compensated_raw_gas_value)
    
            #if args.verbose:
                #print("INFO temperature: ", temperature_value, " co2: ", co2_value, " tvoc: ", tvoc_value)

if __name__ == '__main__':
    start_http_server(args.port, args.bind)
    while True:
        get_data()
        sleep(args.polling_interval)
