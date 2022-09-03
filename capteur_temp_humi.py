# Prise de mesure du capteur de température et d'humidité
#--------------------------------------------------------
import dht
from machine import Pin

def sensor():
    sensor = dht.DHT22(Pin(2))
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        if (isinstance(temp, float) and isinstance(hum, float)) or (isinstance(temp, int) and isinstance(hum, int)):
            msg = (b'{0:3.1f},{1:3.1f}'.format(temp, hum))

            # uncomment for Fahrenheit
            #temp = temp * (9/5) + 32.0

            hum = round(hum, 2)
            return(msg)
        else:
            return('Invalid sensor reading')
    except OSError as e:
        return("ERROR: Failed to return sensor information")
