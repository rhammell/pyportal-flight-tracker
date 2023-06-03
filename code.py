import math
import time
import board
import busio
import displayio
import terminalio
import neopixel
import digitalio
import adafruit_imageload
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
from adafruit_datetime import datetime
from adafruit_display_text import label
from circuitpython_base64 import b64encode

# Import secrets file
try:
    from secrets import secrets
except ImportError:
    print("Missing secrets.py file!")
    raise


def map_range(value, in_min, in_max, out_min, out_max):
    ''' Map input value to output range '''

    return out_min + (((value - in_min) / (in_max - in_min)) * (out_max - out_min))

def calculate_pixel_position(lat, lon, image_width, image_height, lat_min, lat_max, lon_min, lon_max):
    ''' Return x/y pixel coordinate for input lat/lon values, for
        given image size and bounds
    '''

    # Calculate x-coordinate
    x = map_range(lon, lon_min, lon_max, 0, image_width)

    # Calculate y-coordinate using the Mercator projection
    lat_rad = math.radians(lat)
    lat_max_rad = math.radians(lat_max)
    lat_min_rad = math.radians(lat_min)
    merc_lat = math.log(math.tan(math.pi/4 + lat_rad/2))
    merc_max = math.log(math.tan(math.pi/4 + lat_max_rad/2))
    merc_min = math.log(math.tan(math.pi/4 + lat_min_rad/2))
    y = map_range(merc_lat, merc_max, merc_min, 0, image_height)

    return int(x), int(y)


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


def build_url(url, params={}):
    ''' Return URL with formatted parameters added '''

    params_str = "&".join(["%s=%s" % (key, value) for key, value in params.items()])
    return url + "?" + params_str


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


# Create display and main group
display = board.DISPLAY
main_group = displayio.Group()
display.root_group = main_group

# Display splash image
splash_group = displayio.Group()
image = displayio.OnDiskBitmap("/splash.bmp")
image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)
splash_group.append(image_sprite)
main_group.append(splash_group)

# Configure WIFI manager
esp32_cs = digitalio.DigitalInOut(board.ESP_CS)
esp32_ready = digitalio.DigitalInOut(board.ESP_BUSY)
esp32_reset = digitalio.DigitalInOut(board.ESP_RESET)
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

# Build Geoapify map URL
map_params = {
    "style": "klokantech-basic",
    "width": display_width * 2,
    "height": display_height * 2,
    "apiKey": secrets["geoapify_key"],
    "format": "png",
    "area": "rect:%f,%f,%f,%f" % (lon_max, lat_max, lon_min, lat_min)
}
map_url = build_url("https://maps.geoapify.com/v1/staticmap", map_params)
print('Geoapify map URL: ' + map_url)

# Build Adafruit IO image convert URL
convert_params = {
    "x-aio-key": secrets["aio_key"],
    "width": display_width,
    "height": display_height,
    "output": "BMP16",
    "url": url_encode(map_url)
}
convert_url = build_url(
    f"https://io.adafruit.com/api/v2/{secrets["aio_username"]}/integrations/image-formatter",
    convert_params
)

# Download converted map image
image_fname = "/map.bmp"
print("Downloading converted image...")
download_file(convert_url, image_fname)

# Display converted map image
map_group = displayio.Group()
image = displayio.OnDiskBitmap(image_fname)
image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)
map_group.append(image_sprite)
main_group.append(map_group)

# Build OpenSky URL
opensky_params = {
    "lamin": lat_min,
    "lamax": lat_max,
    "lomin": lon_min,
    "lomax": lon_max
}
opensky_url = build_url(
    "https://opensky-network.org/api/states/all",
    opensky_params
)
print('OpenSky search URL:' + opensky_url)

# Build request headers
auth_credentials = secrets["opensky_username"] + ":" + secrets["opensky_password"]
auth_token = b64encode(auth_credentials.encode("utf-8")).decode("ascii")
headers = {'Authorization': 'Basic ' + auth_token}

# Load aircraft icon sheet
tile_size = 16
icon_sheet, palette = adafruit_imageload.load(
    "icons.bmp",
    bitmap=displayio.Bitmap,
    palette=displayio.Palette,
)
palette.make_transparent(0)

# Create aircraft display group
aircraft_group = displayio.Group()
main_group.append(aircraft_group)

# Create time label and display group
time_label = label.Label(
    font = terminalio.FONT,
    color=0x000000,
    background_color=0xFFFFFF,
    #anchor_point=(1.0,0),
    #anchored_position=(display_width-5,5),
    anchor_point=(0,0),
    anchored_position=(5,5),
    padding_top = 2,
    padding_bottom = 2,
    padding_left = 2,
    padding_right = 2
)
time_group  = displayio.Group()
time_group.append(time_label)
main_group.append(time_group)

# Processing loop
while True:

    # Request Opensky data
    print('Requesting data from Opensky...')
    response = wifi.get(opensky_url, headers=headers)
    data = response.json()

    # Parse Opensky response
    unix_time = data["time"]
    states = data["states"]
    time_str = str(datetime.fromtimestamp(unix_time))
    print("Opensky data collected at " + time_str)
    print("Number of aircraft inside bounds: %s" % (len(states) if states else 0))

    # Update time label
    time_label.text = time_str

    # Clear previous aircraft icons
    while len(aircraft_group):
        aircraft_group.pop(-1)

    # Process aircraft data
    if states:
        for state in states:

            # Get position data
            lon = state[5]
            lat = state[6]
            track = state[10]

            # Skip aircraft with empty data
            if not lat or not lon or not track:
                continue

            # Calculate icon x/y coordinate
            x, y =  calculate_pixel_position(lat, lon, display_width, display_height, lat_min, lat_max, lon_min, lon_max)

            # Calculate icon tile index
            tile_index = int((track + 23) / 45)

            # Add aircraft icon
            icon = displayio.TileGrid(
                icon_sheet,
                pixel_shader=palette,
                tile_width = tile_size,
                tile_height = tile_size,
                default_tile=tile_index,
                x = x,
                y = y
            )
            aircraft_group.append(icon)

    # Delay between loops
    time.sleep(30)
