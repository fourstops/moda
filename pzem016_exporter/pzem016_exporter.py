import os
import time
from datetime import datetime
import logging
import argparse

from pzem import PZEM_016
from prometheus_client import start_http_server, Gauge, Histogram, Counter

import json

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus


DEFAULT_MQTT_BROKER_IP = "localhost"
DEFAULT_MQTT_BROKER_PORT = 1883
DEFAULT_MQTT_TOPIC = "pzem"
DEFAULT_READ_INTERVAL = 5
DEFAULT_TLS_MODE = False
DEFAULT_USERNAME = None
DEFAULT_PASSWORD = None


# mqtt callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected OK")
    else:
        print("Bad connection Returned code=", rc)


def on_publish(client, userdata, mid):
   print("mid: " + str(mid))

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("pzem_exporter.log"),
              logging.StreamHandler()],
    datefmt='%Y-%m-%d %H:%M:%S')

DEBUG = os.getenv('DEBUG', 'false') == 'true'

pzem = PZEM_016("/dev/ttyUSB1")  # Replace with the correct pa>

VOLTAGE = Gauge('voltage','Voltage measured (V)')
CURRENT = Gauge('current','Current measured in amps (A)')
WATTS = Gauge ('watts','Power consumption measured (W)')
ENERGY = Gauge ('energy','Energy measured (W-hr)')
FREQUENCY = Gauge ('frequency','AC frequency measured (Hz)')
POWER_FACTOR= Gauge ('power_factor','Power effeciency (%)')
ALARM = Gauge ('alarm', 'alarm status (boolean)')

def get_readings(): 
    reading = pzem.read()
    voltage = "Voltage", reading["voltage"]
    current = "Current", reading["current"]
    watts = "Watts", reading["power"]
    energy = "Energy", reading["energy"]
    frequency = "Frequency", reading["frequency"]
    power_factor = "Power_Factor", reading["power_factor"]
    alarm_status = "Alarm_Status", reading["alarm_status"]

    VOLTAGE.set(reading["voltage"])
    CURRENT.set(reading["current"])
    WATTS.set(reading["power"])
    ENERGY.set(reading["energy"])
    FREQUENCY.set(reading["frequency"])
    POWER_FACTOR.set(reading["power_factor"])
    ALARM.set(reading["alarm_status"])
    return reading

def collect_all_data():
    """Collects all the data currently set"""
    sensor_data = {}
    sensor_data['voltage'] = VOLTAGE.collect()[0].samples[0].value
    sensor_data['current'] = CURRENT.collect()[0].samples[0].value
    sensor_data['watts'] = WATTS.collect()[0].samples[0].value
    sensor_data['energy'] = ENERGY.collect()[0].samples[0].value
    sensor_data['frequency'] = FREQUENCY.collect()[0].samples[0].value
    sensor_data['power_factor'] = POWER_FACTOR.collect()[0].samples[0].value
    sensor_data['alarm'] = ALARM.collect()[0].samples[0].value
    return sensor_data

def str_to_bool(value):
    if value.lower() in {'false', 'f', '0', 'no', 'n'}:
        return False
    elif value.lower() in {'true', 't', '1', 'yes', 'y'}:
        return True
    raise ValueError('{} is not a valid boolean value'.format(value))


def main() -> None:
   
    while True:
        reading = pzem.read()
        timestamp = datetime.utcfromtimestamp(reading["timestamp"])
        alarm_status = 1 if reading["alarm_status"] else 0
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b", "--bind", 
        metavar='ADDRESS', 
        default='0.0.0.0', 
        help="Specify alternate bind address [default: 0.0.0.0]"
    )
    parser.add_argument(
       "-p", "--port", 
       metavar='PORT', 
       default=8000, 
       type=int, 
       help="Specify alternate port [default: 8000]"
    )
    parser.add_argument(
       "-d", "--debug", 
       metavar='DEBUG', 
       type=str_to_bool, 
       help="Turns on more verbose logging, showing sensor output and post responses [default: false]"
    )
    parser.add_argument(
        "--broker",
        default=DEFAULT_MQTT_BROKER_IP,
        type=str,
        help="mqtt broker IP",
    )
    parser.add_argument(
        "--mqttport",
        default=DEFAULT_MQTT_BROKER_PORT,
        type=int,
        help="mqtt broker port",
    )
    parser.add_argument(
        "--topic", default=DEFAULT_MQTT_TOPIC, type=str, help="mqtt topic"
    )
    parser.add_argument(
        "--interval",
        default=DEFAULT_READ_INTERVAL,
        type=int,
        help="the read interval in seconds",
    )
    parser.add_argument(
        "--tls",
        default=DEFAULT_TLS_MODE,
        action='store_true',
        help="enable TLS"
    )
    parser.add_argument(
        "--username",
        default=DEFAULT_USERNAME,
        type=str,
        help="mqtt username"
    )
    parser.add_argument(
        "--password",
        default=DEFAULT_PASSWORD,
        type=str,
        help="mqtt password"
    )
    args = parser.parse_args()

    #device_serial_number = get_serial_number()
    device_id = "pzem"

    start_http_server(addr=args.bind, port=args.port)
    if args.debug:
        DEBUG = True

    logging.info("Listening on http://{}:{}".format(args.bind, args.port))

    mqtt_client = mqtt.Client(client_id=device_id)
    if args.username and args.password:
        mqtt_client.username_pw_set(args.username, args.password)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_publish = on_publish

    if args.tls is True:
        mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)

    if args.username is not None:
        mqtt_client.username_pw_set(args.username, password=args.password)

    mqtt_client.connect(args.broker, port=args.mqttport)
    mqtt_client.loop_start()

    while True:
        mqtt_client.publish(args.topic, json.dumps(collect_all_data()))
        get_readings()
        if DEBUG:
            logging.info('Sensor data: {}'.format(collect_all_data()))
        time.sleep (5)

