from machine import *
import dht

capteur = dht.DHT22(machine.Pin(38))

def capteur():
    global temp, hum
    temp = hum = 0
    try:
        capteur.measure()
        temp = capteur.temperature()
        hum = capteur.humidity()
        if (isinstance(temp, float) and isinstance(hum, float)) or (isinstance(temp, int) and isinstance(hum, int)):
            msg = (b'{0:3.1f},{1:3.1f}'.format(temp, hum))

            # uncomment for Fahrenheit
            #temp = temp * (9/5) + 32.0

            hum = round(hum, 2)
            return(msg)
        else:
            return('Lecture du capteur invalide')
    except OSError as e:
        return("Erreur : Impossible d'obtenir un retour du capteur")

print(capteur())