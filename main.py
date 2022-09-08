from machine import * #lib utilisation module ESP32
import dht
from hcsr04 import HCSR04 #lib capteur HCSR-04
import time, utime, wificonnect
import tft_config, st7789 #lib tft pour affichage sur ttgo t-display
import picoweb #affichage de la page web, ajouter utemplate, pgk_ressources et ulogging aux lib
import vga1_bold_16x32, vga2_16x16, vga1_8x8 # font
import time
import capteur_temp_humi


# ------------------------------------------------- WIFI ----------------------------------------------------------------------
#
# enter your wifi ssid and your password
ssid_wifi = "PAROLA_WIFI"
password_wifi = "LilieLuluKelia25"

ipaddress = wificonnect.connectSTA(ssid=ssid_wifi, password=password_wifi)

# ------------------------------------------------ SET UP ------------------------------------------------------------------
# Enter the size of your own tank
hauteur_max_eau = 1.60   # max level of liquid in meter  / hauteur d'eau maxi dans la cuve en m
position_capteur = 0.22  # distance between sensor and max level in meter / distance entre le capteur et le niveau maxi de la cuve en m
dimension_cuve_X = 1.10  # X size of the tank / taille de la cuve en X en m
dimension_cuve_Y = 5.68  # Y size of the tank / taille de la cuve en Y en m
capacite_cuve = int(round(hauteur_max_eau*dimension_cuve_X*dimension_cuve_Y))

# definition PIN module ESP32
frequence_led = 500
led_bleu = PWM(Pin(27, Pin.OUT, 0), frequence_led)
led_verte1 = PWM(Pin(26, Pin.OUT, 0), frequence_led)
led_verte2 = PWM(Pin(25, Pin.OUT, 0), frequence_led)
led_jaune1 = PWM(Pin(33, Pin.OUT, 0), frequence_led)
led_jaune2 = PWM(Pin(32, Pin.OUT, 0), frequence_led)
led_rouge = PWM(Pin(12, Pin.OUT, 0), frequence_led)
buzzer = Pin(15, Pin.OUT, 0)
bouton = Pin(35,Pin.IN, Pin.PULL_UP)

# definition PIN capteur température et humidité
sensor = dht.DHT22(Pin(2))

# definition du display
tfton = not bouton
tft = tft_config.config()
tft.init() # initialisation de l'écran

# definition variables:
surface_cuve = dimension_cuve_X * dimension_cuve_Y
volume_max_cuve = round(surface_cuve * hauteur_max_eau, 2)
volume_disponible = 0.00
timer = Timer(0)

# prise de mesure température et humidité sur capteur DHT22
def mesure_temperature_humidite():
    global temp
    global hum
    global vitesse_son
    temperature_humidite = capteur_temp_humi.sensor()
    if not temperature_humidite == None:
        temp = round(temperature_humidite[0], 2)
        print("")    
        print("temperature = ", temperature_humidite[0])
        hum = round(temperature_humidite[1], 2)
        print("humidite = ",temperature_humidite[1])
        vitesse_son = 331.3 + 0.606 * temp
        print(f"vitesse du son : {vitesse_son}")
        return vitesse_son, temp, hum
    else:
        temp = 15
        hum = 0
        vitesse_son = 331.3 + 0.606 * temp
        screen_error_temp()
        return vitesse_son, temp, hum


# initialisation des LED
def leds_init():
    led_bleu.duty(0)
    led_verte1.duty(0)
    led_verte2.duty(0)
    led_jaune1.duty(0)
    led_jaune2.duty(0)
    led_rouge.duty(0)

# affichage du message d'erreur sur l'écran
def screen_error():
    tft.fill(st7789.BLACK)
    tft.text(vga1_bold_16x32, "MESURE FAILED", 15, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)
    text = "Push RESET"
    length_text=len(text)
    tft.text(vga1_bold_16x32, text, tft.width() // 2 - length_text // 2 * vga1_bold_16x32.WIDTH, 2 * tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.BLACK)


def screen_error_temp():
    text = f"T: {str(temp)} deg    -    H: {str(hum)} %"
    length_text = len(text)
    tft.text(vga1_8x8, text, tft.width() // 2 - length_text // 2 * vga1_8x8.WIDTH, 120, st7789.RED, st7789.YELLOW)


# eclairage de la led selon le niveau de liquide mesuré
def affichage_analogique():
    global volume_disponible
    leds_init()
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

# calcul du volume de liquide présent dans la cuve
def calcul_volume():
    global volume_disponible
    global temp
    data = []
    try:
        for i in range(1, 10):
            mesure = HCSR04(trigger_pin=22, echo_pin=21)
            distance_mesuree = mesure.distance_cm() / 100
            data.append(distance_mesuree)
            print("mesure ", i ,": ", distance_mesuree)
            time.sleep(0.05)
        distance_moyenne = sum(data)/len(data)
        distance_moyenne_corrigee = (distance_moyenne * temp) / 19.5
        if distance_moyenne > 0:
            print(f"distance moyenne : {distance_moyenne}m")
            print(f"distance utilisée : {distance_moyenne_corrigee}m")
            volume_disponible_avant_correction = round(((hauteur_max_eau + position_capteur) * surface_cuve) - (distance_moyenne * surface_cuve), 2)
            print(f"Volume avant correction : {volume_disponible_avant_correction}m3")
            volume_disponible = round(((hauteur_max_eau + position_capteur) * surface_cuve) - (distance_moyenne_corrigee * surface_cuve), 2)
            print(f"Volume disponible utilisé: {volume_disponible}m3")
            return volume_disponible
        else:
            print("Distance mesurée <= 0, problème de réception capteur")
            screen_error()       
    except:
        print('EXPECT : MEASUREMENT FAILED - SENSOR HCSR KO')
        screen_error()

# affichage des informations sur l'écran 
def affichage_numerique():
    global volume_disponible
    global temp
    global hum
    if volume_max_cuve > volume_disponible >= 0.1*volume_max_cuve:
        tft.fill(st7789.BLACK)
        tft.text(vga1_bold_16x32, "NIVEAU CUVE", 35, 10, st7789.CYAN)
        tft.text(vga2_16x16, f"Capacite: {str(capacite_cuve)}m3", 6, 55, st7789.YELLOW)
        text = f"Reste: {str(volume_disponible)} m3"
        length_text = len(text)
        tft.text(vga2_16x16, text, tft.width() // 2 - length_text // 2 * vga2_16x16.WIDTH, 80, st7789.GREEN)
    elif 0 <= volume_disponible < 0.1*volume_max_cuve:
        tft.fill(st7789.YELLOW)
        tft.text(vga1_bold_16x32, "CUVE VIDE", 45, tft.height() // 3 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
        tft.text(vga1_bold_16x32, "NIVEAU < 1 m3", 15, (tft.height() // 3)*2 - vga1_bold_16x32.HEIGHT//2, st7789.RED, st7789.YELLOW)
    elif volume_disponible >= volume_max_cuve:
        tft.fill(st7789.CYAN)
        tft.text(vga1_bold_16x32, "CUVE PLEINE ", 40, tft.height() // 2 - vga1_bold_16x32.HEIGHT//2, st7789.BLUE, st7789.CYAN)
    else:
        screen_error()
    if temp == 15 or hum == 0:
        screen_error_temp()
    else:
        text = f"T: {str(temp)} deg  -  H: {str(hum)} %"
        length_text = len(text)
        tft.text(vga1_8x8, text, tft.width() // 2 - length_text // 2 * vga1_8x8.WIDTH, 120, st7789.CYAN)

# Mise sous tension de l'écran
def bouton_push(p):
    global tfton
    tfton = True
    tft.on()
    affichage_numerique()

# gestion du programme selon l'état de l'écran:
def handleInterrupt(timer):
    global tfton
    global volume_disponible
    global vitesse_son
    mesure_temperature_humidite()
    mesure_volume = calcul_volume()
    if mesure_volume:
        if tfton:
            tft.on()
            affichage_analogique()
            affichage_numerique()
            tfton = False
        else:
            tft.off()
            affichage_analogique()
    else:
        print("ERROR : Impossible mesurement")



# ---------------------------------------------------------
# --------------------- START PROGRAMME -------------------
# Ecran de démarrage
tft.fill(st7789.GREEN)
tft.text(vga1_bold_16x32, " POWER ON", 45, 10, st7789.RED, st7789.GREEN)
tft.text(vga1_bold_16x32, "NIVEAU DE", 45, 50, st7789.BLUE, st7789.GREEN)
tft.text(vga1_bold_16x32, "LA CUVE :", 50, 85, st7789.BLUE, st7789.GREEN)
time.sleep(4)

# utilisation du bouton poussoir de la board pour allumer l'écran
bouton.irq(trigger=Pin.IRQ_FALLING, handler=bouton_push)

# relance de la prise de mesure toutes les 10 secondes
timer.init(period=10000, mode=Timer.PERIODIC, callback=handleInterrupt)

# ---- Routing Picoweb ------------------------------------ 
app = picoweb.WebApp(__name__)
@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from app.sendfile(resp, '/web/index.html')

@app.route("/get_data")
def get_volume(req, resp):
    global volume_disponible
    global temp
    global hum
    yield from picoweb.jsonify(resp, {'volume': volume_disponible, 'temperature': temp, 'humidite': hum})

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

app.run(debug=True, host = ipaddress, port = 80)


