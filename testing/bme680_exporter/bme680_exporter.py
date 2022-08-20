import time
from datetime import datetime
import subproces
import paho.mqtt.publish as publish
import json
from statistics import median
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from gpiozero import CPUTemperature

#--| User Config |-----------------------------------------------
SERVICE_ACCOUNT_FILE = 'credentials.json'
SPREADSHEET_ID = '10HocaIJ3mlkCNWlz_dHiGccNj9j2rZOxzhuilCC8bnM'
DATA_LOCATION = 'A2'
UPDATE_RATE = 30
#--| User Config |-----------------------------------------------

# Google Sheets API setup
SCOPES = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/drive']
CREDS = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
SHEET = build('sheets', 'v4', credentials=CREDS).spreadsheets()

#Open C File
proc = subprocess.Popen(['./bsec_bme680'], stdout=subprocess.PIPE)

listIAQ = []
listCO2 = []
listVOC = []
listTemperature = []
listHumidity  = []
listPressure = []
listGas = []
listStatic_IAQ = []
listRaw_Temperature = []
listRaw_Humidity = []
listIAQ_Accuracy = []
listBSEC_Status = []

for line in iter(proc.stdout.readline, ''):
    lineJSON = json.loads(line.decode("utf-8")) # process line-by-line
    lineDict = dict(lineJSON)

    listIAQ.append(float(lineDict['IAQ']))
    listCO2.append(float(lineDict['CO2']))
    listVOC.append(float(lineDict['VOC']))
    listTemperature.append(float(lineDict['Temperature']))
    listHumidity.append(float(lineDict['Humidity']))
    listPressure.append(float(lineDict['Pressure']))
    listGas.append(float(lineDict['Gas']))
    listStatic_IAQ.append(float(lineDict['Static_IAQ']))
    listRaw_Temperature.append(float(lineDict['Raw_Temperature']))
    listRaw_Humidity.append(float(lineDict['Raw_Humidity']))
    listIAQ_Accuracy.append(int(lineDict['IAQ_Accuracy']))
    listBSEC_Status.append(int(lineDict['BSEC_Status']))

    if len(listIAQ_Accuracy) == 20:
        #generate the median for each value
        IAQ = median(listIAQ)
        CO2 = median(listCO2)
        VOC = median(listVOC)
        Temperature = median(listTemperature)
        Humidity = median(listHumidity)
        Pressure = median(listPressure)
        Gas = median(listGas)
        Static_IAQ = median(listStatic_IAQ)
        Raw_Temperature = median(listRaw_Temperature)
        Raw_Humidity = median(listRaw_Humidity)
        IAQ_Accuracy = median(listIAQ_Accuracy)
        BSEC_Status = median(listBSEC_Status)

        #clear lists
        listIAQ.clear()
        listCO2.clear()
        listVOC.clear()
        listTemperature.clear()
        listHumidity.clear()
        listPressure.clear()
        listGas.clear()
        listRaw_Temperature.clear()
        listRaw_Humidity.clear()
        listIAQ_Accuracy.clear()
        listBSEC_Status.clear()

        #Temperature Offset
        Temperature = Temperature + 2
        values = [[datetime.now().isoformat(), IAQ,
                                CO2,
                                VOC,
                                Temperature,
                                Humidity,
                                Pressure,
                                Gas,
                                Static_IAQ,
                                Raw_Temperature,
                                Raw_Humidity,
                                BSEC_Status]]
        SHEET.values().append(spreadsheetId=SPREADSHEET_ID,
                                valueInputOption='RAW',
                                range=DATA_LOCATION,
                                body={'values' : values}).execute()
        time.sleep(UPDATE_RATE)
        payload = {"IAQ": round(IAQ, 1), "CO2": round(CO2, 1), "VOC": round(VOC, 1), "Temperature": round(Temperature, 1), "Humidity": round(Humidity, 1), "Pressure": round(Pressure, 1), "Gas": Gas, "BSEC_Status": BSEC_Status}
        publish.single("bme680", json.dumps(payload), hostname="192.168.0.160")
