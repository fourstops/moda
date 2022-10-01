cd  ~/moda
sudo cp -r sgp30-exporter /usr/src/
sudo chown -R pi:pi /usr/src/sgp30-exporter

cd /usr/src/sgp30-exporter
sudo cp ~/moda/services/sgp30-exporter.service /etc/systemd/system/sgp30-exporter.service
sudo chmod 644 /etc/systemd/system/sgp30-exporter.service

sudo systemctl daemon-reload
sudo systemctl start sgp30-exporter
sudo systemctl status sgp30-exporter
sudo systemctl enable sgp30-exporter
