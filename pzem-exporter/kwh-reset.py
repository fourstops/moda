#!/usr/bin/python3

import minimalmodbus

pz = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
pz.serial.baudrate = 9600

pz._perform_command(66, '')
