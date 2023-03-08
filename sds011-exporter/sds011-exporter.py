#!/usr/bin/python3

import os
import argparse
import datetime
import time
import logging
from collections import deque

import paho.mqtt.publish
from prometheus_client import start_http_server, Gauge, Histogram

from sds011 import SDS011
import aqi

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("enviroplus_exporter.log"),
              logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""sds011_exporter.py - Expose readings from the SDS011 Particulate Sensor in Prometheus format
Press Ctrl+C to exit!
""")

DEBUG = os.getenv('DEBUG', 'false') == 'true'

def parse_args():
    parser = argparse.ArgumentParser(description="Measure air quality using an SDS011 sensor.")

    parser.add_argument("-b", "--bind", metavar='ADDRESS', default='0.0.0.0', help="Specify alternate bind address [default: 0.0.0.0]")
    parser.add_argument("-p", "--port", metavar='PORT', default=8000, type=int, help="Specify alternate port [default: 8000]")
    parser.add_argument("--country", "-c", choices=["EU", "US"], default="US", metavar="COUNTRY", help="country code (ISO 3166-1 alpha-2) used to compute AQI. Currently accepted values (default: US) : 'EU' (CAQI) and 'US' (AQI US)")
    parser.add_argument("--delay", "-d", default=15, metavar="SECONDS", type=int, help="seconds to pause after getting data with the sensor before taking another measure (default: 1200, ie. 20 minutes)")
    parser.add_argument("--log", "-l", metavar="FILE", help="path to the CSV file where data will be appended")
    parser.add_argument("--measures", "-m", default=3, metavar="N", type=int, help="get PM2.5 and PM10 values by taking N consecutive measures (default: 3)")
    parser.add_argument("--mqtt-hostname", "-n", metavar="IP/HOSTNAME", help="IP address or hostname of the MQTT broker")
    parser.add_argument("--mqtt-port", "-r", default="1883", metavar="PORT", type=int, help="Port number of the MQTT broker (default: '1883')")
    parser.add_argument("--mqtt-base-topic", "-i", default="sds011", metavar="TOPIC", help="Parent MQTT topic to use (default: 'aqi')")
    parser.add_argument("--omnia-leds", "-o", action="store_true", help="set Turris Omnia LED colors according to measures (User #1 LED for PM2.5 and User #2 LED for PM10)")
    parser.add_argument("--sensor", "-s", default="/dev/ttyUSB0", metavar="FILE", help="path to the SDS011 sensor (default: '/dev/ttyUSB0')")
    parser.add_argument("--sensor-operation-delay", "-e", default=10, metavar="SECONDS", type=int, help="seconds to let the sensor start (default: 10)")
    parser.add_argument("--sensor-start-delay", "-t", default=1, metavar="SECONDS", type=int, help="seconds to let the sensor perform an operation : taking a measure or going to sleep (default: 1)")
    parser.add_argument("-f", "--debug", metavar='DEBUG', type=str_to_bool, help="Turns on more verbose logging, showing sensor output and post responses [default: false]")

    return parser.parse_args()

PM25 = Gauge('PM25', 'Particulate Matter of diameter less than 2.5 microns. Measured in micrograms per cubic metre (ug/m3)')
PM10 = Gauge('PM10', 'Particulate Matter of diameter less than 10 microns. Measured in micrograms per cubic metre (ug/m3)')
AQI = Gauge('AQI', 'AQI value')
AQIc = Gauge('AQIc', 'AQIc value')

PM25_HIST = Histogram('pm25_measurements', 'Histogram of Particulate Matter of diameter less than 2.5 micron measurements', buckets=(0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100))
PM10_HIST = Histogram('pm10_measurements', 'Histogram of Particulate Matter of diameter less than 10 micron measurements', buckets=(0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100))

def get_data(sensor, measures, start_delay, operation_delay):
    # Wake-up sensor
    sensor.sleep(sleep=False)

    current_pm25 = 0.0
    current_pm10 = 0.0

    # Let the sensor at least 10 seconds to start in order to get precise values
    time.sleep(start_delay)

    # Take several measures
    for _ in range(measures):
        x = sensor.query()
        current_pm25 = current_pm25 + x[0]
        current_pm10 = current_pm10 + x[1]
        time.sleep(operation_delay)

    # Round the measures as a number with one decimal
    current_pm25 = round(current_pm25/measures, 1)
    current_pm10 = round(current_pm10/measures, 1)
    current_aqi = aqi.to_iaqi(aqi.POLLUTANT_PM25, current_pm25, algo=aqi.ALGO_EPA)
    current_aqic = aqi.to_aqi([(aqi.POLLUTANT_PM25, current_pm25), (aqi.POLLUTANT_PM10, current_pm10)])

    # Put the sensor to sleep
    sensor.sleep(sleep=True)
    time.sleep(operation_delay)

    PM25.set(current_pm25)
    PM10.set(current_pm10)
    AQI.set(current_aqi)
    AQIc.set(current_aqic)

    PM25_HIST.observe(current_pm25)
    PM10_HIST.observe(current_pm10 - current_pm25)

    return current_pm25, current_pm10, current_aqi, current_aqic

def set_turris_omnia_led(user1_color, user2_color):
    if user1_color != "":
        # LED User #1 ("A")
        with open("/sys/class/leds/omnia-led:user1/autonomous", "w") as led_user1_autonomous:
            led_user1_autonomous.write("0\n")
        # LED User #1 ("A")
        with open("/sys/class/leds/omnia-led:user1/color", "w") as led_user1_color:
            led_user1_color.write(user1_color + "\n")

    if user2_color != "":
        # LED User #2 ("B")
        with open("/sys/class/leds/omnia-led:user2/autonomous", "w") as led_user2_autonomous:
            led_user2_autonomous.write("0\n")
        # LED User #2 ("B")
        with open("/sys/class/leds/omnia-led:user2/color", "w") as led_user2_color:
            led_user2_color.write(user2_color + "\n")

def save_log(logfile, logged_pm25, logged_pm10, logged_aqi):
    try:
        with open(logfile, "a") as log:
            dt = datetime.datetime.now()
            log.write("{},{},{},{}\n".format(dt, logged_pm25, logged_pm10, logged_aqi))
            log.close()
    except:
        print("[INFO] Failure in logging data") 

def publish_mqtt(mqtt_hostname, mqtt_port, mqtt_messages):
    try:
        paho.mqtt.publish.multiple(mqtt_messages, hostname=mqtt_hostname, port=mqtt_port, client_id="get_aqi.py")
    except:
        print("[INFO] Failure in publishing to MQTT broker")

def collect_all_data():
    """Collects all the data currently set"""
    sensor_data = {}
    sensor_data['pm25'] = PM25.collect()[0].samples[0].value
    sensor_data['pm10'] = PM10.collect()[0].samples[0].value
    sensor_data['aqi'] = AQI.collect()[0].samples[0].value
    sensor_data['aqic'] = AQIc.collect()[0].samples[0].value

    return sensor_data

def str_to_bool(value):
    if value.lower() in {'false', 'f', '0', 'no', 'n'}:
        return False
    elif value.lower() in {'true', 't', '1', 'yes', 'y'}:
        return True
    raise ValueError('{} is not a valid boolean value'.format(value))

args = parse_args()
sensor = SDS011(args.sensor)


# Start up the server to expose the metrics.
start_http_server(addr=args.bind, port=args.port)
# Generate some requests.
logging.info("Listening on http://{}:{}".format(args.bind, args.port))



while(True):
    # Retrieve current PM2.5 and PM10 values from the sensor
    current_pm25, current_pm10, current_aqi, current_aqic = get_data(sensor, args.measures, args.sensor_start_delay, args.sensor_operation_delay)

    # Set Turris Omnia User #1 and #2 LED colors
    if args.omnia_leds is True:
        color_aqi_pm25 = get_aqi_color(aqi_level["level"], args.country)
        color_aqi_pm10 = get_aqi_color(aqi_level["level"], args.country)

        set_turris_omnia_led(color_aqi_pm25, color_aqi_pm10)

    # Save measured values and AQI level to a log file 
    if args.log is not None:
        save_log(args.log, current_pm25, current_pm10, aqi)

    # Publish measured values and AQI level to an MQTT broker
    if args.mqtt_hostname is not None:
        # Remove any trailing '/' in topic
        topic = args.mqtt_base_topic
        if args.mqtt_base_topic.endswith("/"):
            topic = args.mqtt_base_topic.rstrip("/")

        # List of messages to publish, list of tuples.
        # The tuples are of the form ("<topic>", "<payload>", qos, retain).
        # topic must be present and may not be empty
        msg_aqi = (topic + "/aqi", str(aqi), 0, False)
        msg_level = (topic + "/level", str(aqi_level), 0, False)
        msg_current_pm25 = (topic + "/current_pm25", str(current_pm25), 0, False)
        msg_current_pm10 = (topic + "/current_pm10", str(current_pm10), 0, False)

        messages = [msg_aqi, msg_level, msg_current_pm25, msg_current_pm10]

        # Publish the messages to the MQTT broker
        publish_mqtt(args.mqtt_hostname, args.mqtt_port, messages)

    # Wait before taking the next measure with the sensor
    time.sleep(args.delay)
