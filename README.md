## moda

_a Prometheus exporter variety pack_
<br>
<br>

|   Sensor   | Metric                                                                               |
| :--------: | :----------------------------------------------------------------------------------- |
|  _CCS811_  | Total Volatile Organic Compounds (TVOCs), including equivalent carbon dioxide (eCO2) |
|  _BME680_  | Temperature, Relative Humidity. Pressure, VOCs                                       |
| _PZEM-016_ | AC Volts, Amps, Watts, kWh, Hertz, Power Factor                                      |
|  _SDS011_  | PM2.5, PM10                                                                          |

€<br>
<br>

- **_Dependencies_**

```bash
git clone https://github.com/fourstops/moda
cd moda

pip install prometheus-client
pip install paho-mqtt
pip install python-pzem
pip install py-sds011
pip install minimalmodbus
pip install smbus2
pip install aqipy
pip install adafruit-circuitpython-ccs811
pip install adafruit-circuitpython-sgp40
pip install adafruit-circuitpython-bme680
```

- **pzem-exporter module**

```bash
cd  ~/moda
sudo cp -r pzem-exporter /usr/src/
sudo chown -R pi:pi /usr/src/pzem-exporter

cd /usr/src/pzem-exporter
sudo cp ~/moda/services/pzem-exporter.service /etc/systemd/system/pzem-exporter.service
sudo chmod 644 /etc/systemd/system/pzem-exporter.service

sudo systemctl daemon-reload
sudo systemctl start pzem-exporter
sudo systemctl status pzem-exporter
sudo systemctl enable pzem-exporter

```

- **sds011-exporter module**

```bash
cd  ~/moda
sudo cp -r sds011-exporter /usr/src/
sudo chown -R pi:pi /usr/src/sds011-exporter

cd /usr/src/sds011-exporter
sudo cp ~/moda/services/sds011-exporter.service /etc/systemd/system/sds011-exporter.service
sudo chmod 644 /etc/systemd/system/sds011-exporter.service

sudo systemctl daemon-reload
sudo systemctl start sds011-exporter
sudo systemctl status sds011-exporter
sudo systemctl enable sds011-exporter
```

<br>

- **stemma-exporter module**

```bash
cd  ~/moda
sudo cp -r stemma-exporter /usr/src/
sudo chown -R pi:pi /usr/src/stemma-exporter

cd /usr/src/stemma-exporter
sudo cp ~/moda/services/stemma-exporter.service /etc/systemd/system/stemma-exporter.service
sudo chmod 644 /etc/systemd/system/stemma-exporter.service

sudo systemctl daemon-reload
sudo systemctl start stemma-exporter
sudo systemctl status stemma-exporter
sudo systemctl enable stemma-exporter


```
