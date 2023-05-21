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

# Processing loop
while True:
  pass