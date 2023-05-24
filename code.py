import math
import time
import board
import busio
import displayio
from digitalio import DigitalInOut
import neopixel
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager

# Import secrets file
try:
    from secrets import secrets
except ImportError:
    print("Missing secrets.py file!")
    raise

# Display splash image
splash = displayio.Group()
image = displayio.OnDiskBitmap("/splash.bmp")
image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)
splash.append(image_sprite)
board.DISPLAY.show(splash)

# Configure WIFI manager
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

# Connect WiFi
print('Connecting to wifi...')
wifi.connect()

# Define map center
center_lat = 40.7831
center_lon = -73.9712

# Processing loop
while True:
  pass