from machine import * #lib utilisation module ESP32
from hcsr04 import HCSR04 #lib capteur HCSR-04
import time, utime, wificonnect
import tft_config, st7789 #lib tft pour affichage sur ttgo t-display
import picoweb #affichage de la page web, ajouter utemplate, pgk_ressources et ulogging aux lib
import vga1_bold_16x32, vga2_16x16 # font
import dht
import test_capteur_temp_humi


# ------------------------------------------ WIFI CONNECT ----------------------------------------------------------------------
# enter your wifi ssid and your password
ssid_wifi = PAROLA_WIFI
password_wifi = LilieLuluKelia25

# ------------------------------------------ TANK SIZE -------------------------------------------------------------------------
# Enter the size of your own tank

# définition taille de la cuve
hauteur_max_eau = 1.60   # max level of liquid in meter  / hauteur d'eau maxi dans la cuve en m
position_capteur = 0.22  # distance between sensor and max level in meter / distance entre le capteur et le niveau maxi de la cuve en m
dimension_cuve_X = 1.10  # X size of the tank / taille de la cuve en X en m
dimension_cuve_Y = 5.68  # Y size of the tank / taille de la cuve en Y en m
capacite_cuve = round(hauteur_max_eau*dimension_cuve_X*dimension_cuve_Y, 0)

# -------------------------------------------------------------------------------------------------------------------------------


# definition pin module
frequence_led = 500
led_bleu = PWM(Pin(27, Pin.OUT, 0), frequence_led)
led_verte1 = PWM(Pin(26, Pin.OUT, 0), frequence_led)
led_verte2 = PWM(Pin(25, Pin.OUT, 0), frequence_led)
led_jaune1 = PWM(Pin(33, Pin.OUT, 0), frequence_led)
led_jaune2 = PWM(Pin(32, Pin.OUT, 0), frequence_led)
led_rouge = PWM(Pin(12, Pin.OUT, 0), frequence_led)
capteur = dht.DHT22(machine.Pin(38))
buzzer = Pin(15, Pin.OUT, 0)
bouton = Pin(35,Pin.IN, Pin.PULL_UP)


# definition du display
tfton = not bouton
tft = tft_config.config()
tft.init() # initialisation de l'écran

# definition variables:
surface_cuve = dimension_cuve_X * dimension_cuve_Y
volume_max_cuve = round(surface_cuve * hauteur_max_eau, 2)
volume_disponible = 0.00
timer = Timer(0)

# connexion au wifi
ipaddress = wificonnect.connectSTA(ssid=ssid_wifi, password=password_wifi)

def leds_init():
    led_bleu.duty(0)
    led_verte1.duty(0)
    led_verte2.duty(0)
    led_jaune1.duty(0)
    led_jaune2.duty(0)
    led_rouge.duty(0)

def calcul_volume():
    data = []
    try:
        for i in range(1, 10):
            mesure = HCSR04(trigger_pin=22, echo_pin=21)
            distance = mesure.distance_cm() / 100
            data.append(distance)
            print(distance)
            time.sleep(0.05)
        distance_moyenne = sum(data)/len(data)
        volume_disponible = round(((hauteur_max_eau + position_capteur) * surface_cuve) - (distance_moyenne * surface_cuve), 2)
        print("Distance: ", distance_moyenne, " m\nVolume disponible: ", volume_disponible, " m3")
        return volume_disponible
    except:
        print('erreur prise de mesure')
        error()
        volume_disponible = 0
        return volume_disponible
        pass
        
def affichage_analogique():
    global volume_disponible
    nouveau_volume = calcul_volume() #  round(volume_disponible+.1, 2) #
    print(nouveau_volume)
    if nouveau_volume != volume_disponible:
        leds_init()
        volume_disponible = nouveau_volume
        if volume_max_cuve > volume_disponible >= 0.1*volume_max_cuve:
            if volume_disponible >= 0.9*volume_max_cuve:
                led_bleu.duty(50)
            elif 0.8*volume_max_cuve <= volume_disponible < 0.9*volume_max_cuve:
                led_verte1.duty(30)
            elif 0.6*volume_max_cuve <= volume_disponible < 0.8*volume_max_cuve:
                led_verte2.duty(30)
            elif 0.4*volume_max_cuve <= volume_disponible < 0.6*volume_max_cuve:
                led_jaune1.duty(30)
            elif 0.2*volume_max_cuve <= volume_disponible < 0.4*volume_max_cuve:
                led_jaune2.duty(30)
            elif 0.1*volume_max_cuve <= volume_disponible < 0.2*volume_max_cuve:
                led_rouge.duty(10)
        elif 0 <= volume_disponible < 0.1*volume_max_cuve:
            buzzer.on()
            led_rouge.duty(30)
        elif volume_disponible >= volume_max_cuve:
            led_bleu.duty(100)
    else:
        pass

def affichage_numerique():
    global volume_disponible
    if volume_max_cuve > volume_disponible >= 0.1*volume_max_cuve:
        tft.fill(st7789.BLACK)
        tft.text(vga1_bold_16x32, "NIVEAU CUVE", 35, 15, st7789.CYAN)
        tft.text(vga2_16x16, f"Capacite: {str(capacite_cuve)}m3", 6, 60, st7789.YELLOW)
        tft.text(vga2_16x16, "Reste: ", 15, 95, st7789.GREEN)
        tft.text(vga2_16x16, str(volume_disponible), 120, 95, st7789.GREEN)
        tft.text(vga2_16x16, "m3", 190, 95, st7789.GREEN)
    elif 0 <= volume_disponible < 0.1*volume_max_cuve:
        tft.fill(st7789.YELLOW)
        tft.text(vga1_bold_16x32, "CUVE VIDE", 45, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
        tft.text(vga1_bold_16x32, "NIVEAU < 1 m3", 15, (tft.height() // 3)*2 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
    elif volume_disponible >= volume_max_cuve:
        tft.fill(st7789.CYAN)
        tft.text(vga1_bold_16x32, "CUVE PLEINE ", 40, tft.height() // 2 - vga1_bold_16x32.HEIGHT//2, st7789.BLUE, st7789.CYAN)
    else:
        error()

def error():
    tft.fill(st7789.BLACK)
    tft.text(vga1_bold_16x32, "MESURE", 80, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)
    text = "ERRONEE"
    length=len(text)
    tft.text(vga1_bold_16x32, text, tft.width() // 2 - length // 2 * vga1_bold_16x32.WIDTH, 2 * tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)
    
def bouton_push(p):
    global tfton
    tfton = True
    tft.on()
    affichage_numerique()

def capteur_temperature():
    test_capteur_temp_humi.capteur()

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

def handleInterrupt(timer):
    global tfton
    if tfton:
        tft.on()
        affichage_analogique()
        affichage_numerique()
        tfton = False
    else:
        tft.off()
        affichage_analogique()

# ---------------------------------------------------------
# ______ START PROGRAMME_______
tft.fill(st7789.GREEN)
tft.text(vga1_bold_16x32, " POWER ON", 45, 10, st7789.RED, st7789.GREEN)
tft.text(vga1_bold_16x32, "NIVEAU DE", 45, 50, st7789.BLUE, st7789.GREEN)
tft.text(vga1_bold_16x32, "LA CUVE :", 50, 85, st7789.BLUE, st7789.GREEN)
time.sleep(4)


# ---- Routing Picoweb ------------------------------------ 
app = picoweb.WebApp(__name__)
@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/index.html')

@app.route("/get_volume")
def get_volume(req, resp):
    global volume_disponible
    yield from picoweb.jsonify(resp, {'volume': volume_disponible})

@app.route("/get_temperature")
def get_volume(req, resp):
    global temp
    yield from picoweb.jsonify(resp, {'temperature': temp})

@app.route("/get_humidite")
def get_volume(req, resp):
    global hum
    yield from picoweb.jsonify(resp, {'temperature': hum})

@app.route("/style.css")
def css(req, resp):
    print("Send style.css")
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/style.css')
    
@app.route("/goutte_eau.jpg")
def index(req, resp):
    print("Send JPG")
    yield from picoweb.start_response(resp)
    try:
        with open("web/goutte_eau.jpg", 'rb') as img_binary:
            img= img_binary.read()
        yield from resp.awrite(img)
    except Exception:
        print("Image file not found.")
        pass

bouton.irq(trigger=Pin.IRQ_FALLING, handler=bouton_push)
timer.init(period=10000, mode=Timer.PERIODIC, callback=handleInterrupt)
app.run(debug=True, host = ipaddress, port = 80)