# from datetime import datetime
from utime import localtime
import requests
import wificonfig

def send_data(volume_value):
    api_key = wificonfig.api_key

    date = localtime()
    mois = str(localtime().tm_mon).zfill(2)
    date = f"{localtime().tm_mday}.{mois}.{localtime().tm_year} {localtime().tm_hour}:{localtime().tm_min}:{localtime().tm_sec}"

    niveau = "?date="+ date + "&niveau="+ str(volume_value)
    try:
        request_headers = {'Content-Type': 'application/x-www-form-urlencoded' }
        url = f'https://script.google.com/macros/s/{api_key}/exec{niveau}'
        request = requests.get(url, headers=request_headers)
        request.close()

    except OSError as e:
        print('Failed to read/publish sensor readings.')