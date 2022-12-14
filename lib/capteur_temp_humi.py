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
        if temp and hum:
            # uncomment for Fahrenheit
            #temp = temp * (9/5) + 32.0
            return temp, hum
        else:
            print('Invalid temperature sensor reading')
            print('Temp value use : 15°C')
            return None
    except:
        print("EXCEPT ERROR: Failed to return temperature sensor information")
        print("EXCEPT ERROR : temp value use : 15°C")
        return None
