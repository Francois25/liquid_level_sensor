from utime import localtime
import urequests as requests
import wificonfig

def send_data(volume_value):
    """Send value of water tank volume to a google sheet for annual analyse

    Args:
        volume_value (float): Volume of water remain in tank
    """
    api_key = wificonfig.api_key
    volume = str(volume_value)
    volume = volume.replace(".", ",")
    niveau = "?niveau="+ volume

    try:
        request_headers = {'Content-Type': 'application/x-www-form-urlencoded' }
        url = 'https://script.google.com/macros/s/' + api_key + '/exec' + niveau
        print(url)
        request = requests.get(url, headers=request_headers)
        request.close()
        print(f"Donnée sauvegarder: {volume_value}")

    except OSError as e:
        print('Failed to read/publish sensor readings.')
    