# Liquid_level_sensor presentation :

Ultrasonic sensor for measuring the height of a liquid in a rectangular tank with analogue display of the data by means of coloured LEDs, the analogue display is done on the screen of an ESP32-TTGO-T-Display and an internet page.

# Micropython firmware :
The firmware used is Micropython, downloadable here: [MicroPython firmware for ESP32](https://micropython.org/download/esp32spiram/)  
The use of Picoweb allows to transmit the information on the web page using the address corresponding to the IP of the ESP card

# How it works : 
The ultrasonic sensor used here is the HCSR04. Coupled to this sensor is another temperature and humidity sensor, the DHT22 in order to calibrate the speed of sound in relation to temperature and humidity. In my case, the humidity had very little influence on the value of the ultrasonic measurement, so I didn't pay attention to it.
In the main.py file it is necessary to enter your own SSId and password on lines 15 and 16.

If there is a problem with the ultrasonic sensor, the screen will display an error message in red on a black background, so check the status of the sensor in the tank.
If there is a problem with the temperature sensor, the screen displays in red on a yellow background the temperature at 15° and the humidity at 0%.

All the libraries for the project to be functional can be found in the folder [/lib] folder (https://github.com/Francois25/liquid_level_sensor/tree/master/lib)
All the fonts for the project to be functional are in the folder [/font](https://github.com/Francois25/liquid_level_sensor/tree/master/font)

# Addon :
The files needed to make the project work are in the folder [/Docs](https://github.com/Francois25/liquid_level_sensor/tree/master/Docs), you have BOM for buy all the parts you need, and a wiring diagram and Gerber ZIP.
You can find all 3D files for print different parts on folder [/STL](https://github.com/Francois25/liquid_level_sensor/tree/master/STL)

# Acknowledgements:
A big thank you to my friend Roel Jaspers who is always there when I get stuck on the code... Big Up Cyberjunkie.
