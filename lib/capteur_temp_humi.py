# Prise de mesure du capteur de température et d'humidité
#--------------------------------------------------------
import dht
from machine import Pin

temp = 0.00
hum = 0.00

def sensor():
    sensor = dht.DHT22(Pin(2))
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        if temp and hum:#(isinstance(temp, float) and isinstance(hum, float)) or (isinstance(temp, int) and isinstance(hum, int)):
            #msg = (b'{0:3.1f},{1:3.1f}'.format(temp, hum))

            # uncomment for Fahrenheit
            #temp = temp * (9/5) + 32.0

            #hum = round(hum, 2)
            #return(msg)
            return temp, hum
        else:
            return('Invalid sensor reading')
    except OSError as e:
        return("ERROR: Failed to return sensor information")
