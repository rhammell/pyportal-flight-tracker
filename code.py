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
    

def get_bounds(lat, lon, distance, ratio=1):
    ''' Return min/max bounds for box centered on input
        lat/lon coordinate for input distance
        
        Ratio parameter determines the width:height ratio
        of the resulting box dimensions
    '''

    # Set earth radius
    EARTH_RADIUS = 6378.1

    # Convert to radians
    rad_lat = math.radians(lat)
    rad_lon = math.radians(lon)

    # Calculate angular distance in radians
    rad_dist = distance / EARTH_RADIUS
    
    # Calculate distance deltas
    delta_lat = rad_dist
    delta_lon = math.asin(math.sin(rad_dist) / math.cos(rad_lat))
    if ratio < 1:
        delta_lat *= ratio
    else:
        delta_lon *= ratio
        
    # Calculate latitude bounds
    min_rad_lat = rad_lat - delta_lat
    max_rad_lat = rad_lat + delta_lat

    # Calculate longitude bounds
    min_rad_lon = rad_lon - delta_lon
    max_rad_lon = rad_lon + delta_lon
    
    # Convert from radians to degrees
    max_lat = math.degrees(max_rad_lat)
    min_lat = math.degrees(min_rad_lat)
    max_lon = math.degrees(max_rad_lon)
    min_lon = math.degrees(min_rad_lon)

    return max_lat, min_lat, max_lon, min_lon
    

def url_encode(string):
    ''' Return URL encoding of input string '''

    encoded_string = ''
    for char in string:
        if char.isalpha() or char.isdigit() or char in ('-', '_', '.', '~'):
            encoded_string += char
        else:
            encoded_string += '%' + '{:02X}'.format(ord(char))
    
    return encoded_string
    
def download_file(url, fname, chunk_size=4096, headers=None):
    ''' Download file from URL and store locally '''

    # Request url
    response = wifi.get(url, stream=True)

    # Determine content length from response
    headers = {}
    for title, content in response.headers.items():
        headers[title.lower()] = content
    content_length = int(headers["content-length"])

    # Save streaming data to output file
    remaining = content_length
    print("Saving data to ", fname)
    stamp = time.monotonic()
    with open(fname, "wb") as file:
        for i in response.iter_content(min(remaining, chunk_size)):
            remaining -= len(i)
            file.write(i)
            if not remaining:
                break
    response.close() 
   
   
# Display splash image
splash_group = displayio.Group()
image = displayio.OnDiskBitmap("/splash.bmp")
image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)
splash_group.append(image_sprite)
board.DISPLAY.show(splash_group)

# Configure WIFI manager
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

# Connect WiFi
print("Connecting to wifi...")
wifi.connect()

# Define map center
center_lat = 40.7831
center_lon = -73.9712

# Map distance (km)
distance = 20

# Display dimensions
display_width = board.DISPLAY.width
display_height = board.DISPLAY.height
aspect_ratio = display_width / display_height

# Calculate bounds
print("Calculating map bounds...")
lat_max, lat_min, lon_max, lon_min = get_bounds(center_lat, center_lon, distance, ratio=aspect_ratio)

# Geoapify map URL parameters
map_params = {
    "style": "klokantech-basic",
    "width": display_width * 2,
    "height": display_height * 2,
    "apiKey": secrets["geoapify_key"],
    "format": "png",
    "area": "rect:%f,%f,%f,%f" % (lon_max, lat_max, lon_min, lat_min)
}

# Build Geoapify map URL
map_params_str = "&".join(["%s=%s" % (key, value) for key, value in map_params.items()])
map_url = "https://maps.geoapify.com/v1/staticmap?" + map_params_str
print('Geoapify map URL: ')
print(map_url)

# Adafruit IO image convert URL parameters
convert_params = {
    "x-aio-key": secrets["aio_key"],
    "width": display_width,
    "height": display_height,
    "output": "BMP16",
    "url": url_encode(map_url)
}

# Build Adafruit IO image convert URL
convert_params_str = "&".join(["%s=%s" % (key, value) for key, value in convert_params.items()])
convert_url =  f"https://io.adafruit.com/api/v2/{secrets["aio_username"]}/integrations/image-formatter?" + convert_params_str

# Download converted map image
image_fname = "/map.bmp"
print("Downloading converted image...")
download_file(convert_url, image_fname)

# Display converted map image
map_group = displayio.Group()
image = displayio.OnDiskBitmap(image_fname)
image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)
map_group.append(image_sprite)
board.DISPLAY.show(map_group)

# Processing loop
while True:
    pass