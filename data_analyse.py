from utime import localtime
import urequests as requests
import wificonfig

def send_data(volume_value, temp):
    api_key = wificonfig.api_key
    niveau = f"?niveau={str(volume_value)}"

    try:
        request_headers = {'Content-Type': 'application/x-www-form-urlencoded' }
        url = 'https://script.google.com/macros/s/' + api_key + '/exec' + niveau
        print(url)
        request = requests.get(url, headers=request_headers)
        request.close()
        print(f"Donnée sauvegarder: {volume_value}")

    except OSError as e:
        print('Failed to read/publish sensor readings.', e)
    