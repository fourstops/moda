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


#DEFAULT_MQTT_BROKER_IP = "localhost"
#DEFAULT_MQTT_BROKER_PORT = 1883
#DEFAULT_MQTT_TOPIC = "enviroplus"
#DEFAULT_READ_INTERVAL = 5
#DEFAULT_TLS_MODE = False
#DEFAULT_USERNAME = None
#DEFAULT_PASSWORD = None

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
pzem = PZEM_016("/dev/ttyUSB0")  # Replace with the correct pa>

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

def publish_mqtt(mqtt_hostname, mqtt_port, mqtt_messages):
    try:
        paho.mqtt.publish.multiple(mqtt_messages, hostname=mqtt_hostname, port=mqtt_port, client_id="get_aqi.py")
    except:
        print("[INFO] Failure in publishing to MQTT broker")

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bind", metavar='ADDRESS', default='0.0.0.0', help="Specify alternate bind address [default: 0.0.0.0]")
    parser.add_argument("-p", "--port", metavar='PORT', default=8002, type=int, help="Specify alternate port [default: 8000]")
    parser.add_argument("-d", "--debug", metavar='DEBUG', type=str_to_bool, help="Turns on more verbose logging, showing sensor output and post responses [default: false]")
    parser.add_argument( "--broker", default='192.168.0.103', type=str, help="mqtt broker IP")
    parser.add_argument("--mqttport", default=1883, type=int, help="mqtt broker port",)
    parser.add_argument("--topic", default='electric', type=str, help="mqtt topic")
    parser.add_argument("--tls", default=False, action='store_true', help="enable TLS")
    parser.add_argument("--username", default='USERNAME',type=str, help="mqtt username")
    parser.add_argument("--password", default='PASSWORD', type=str, help="mqtt password")
    parser.add_argument("--delay", "-s", default=5, metavar="SECONDS", type=int, help="seconds to pause after getting data with the sensor before taking another measure")
    args = parser.parse_args()

    logging.info("Listening on http://{}:{}".format(args.bind, args.port))
    start_http_server(addr=args.bind, port=args.port)

    device_id = "pzem"
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
            try:
                mqtt_client.publish(args.topic, json.dumps(collect_all_data()))
                get_readings()
                time.sleep (args.delay)
            except Exception as e:
                print(e)

if __name__ == "__main__":
    main()
# python3 pzem016_exporter_mqtt.py --port=8002 --broker='192.168.0.103' --mqttport=1883 --username='pi' --password='goldfish' --topic='power'
