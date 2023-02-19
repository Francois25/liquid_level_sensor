from utime import localtime
import requests
import wificonfig

def send_data(volume_value):
    api_key = wificonfig.api_key

    date = localtime()
    mois = str(localtime()[1])#.zfill(2)
    heure = str(localtime()[3])
    minute = str(localtime()[4])
    seconde = str(localtime()[5])
    if len(mois) == 1:
        mois = "0" + mois
    if len(heure) == 1:
        heure = "0" + heure
    if len(minute) == 1:
        minute = "0" + minute
    if len(seconde) == 1:
        seconde = "0" + seconde
    date = f"{localtime()[2]}.{mois}.{localtime()[0]}%{heure}:{minute}:{seconde}"
    
    niveau = "?date="+ date + "&niveau="+ str(volume_value)
    try:
        request_headers = {'Content-Type': 'application/x-www-form-urlencoded' }
        url = f'https://script.google.com/macros/s/{api_key}/exec{niveau}'
        request = requests.get(url, headers=request_headers)
        request.close()
        print("Data saved")

    except OSError as e:
        print('Failed to read/publish sensor readings.')