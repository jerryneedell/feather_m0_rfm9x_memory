import sys
import digitalio
import analogio
import busio
import time
import board
import gc
import storage
SLEEP_SECONDS = 10
voltage_pin = analogio.AnalogIn(board.D9)
radio_cs = digitalio.DigitalInOut(board.RFM9X_CS)
radio_cs.switch_to_output(True)
radio_reset = digitalio.DigitalInOut(board.RFM9X_RST)
sd_cs = digitalio.DigitalInOut(board.D5)


def get_gps_position():
    gc.collect()
    print("gps ",gc.mem_free())
    import adafruit_gps
    uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
    gps = adafruit_gps.GPS(uart, debug=True)
    gps.send_command(b"PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
    gps.send_command(b"PMTK220,1000")
    start = time.monotonic()
    while True:
        gps.update()
        if gps.has_fix:
            print("We have fix!")
            print("gps ",gc.mem_free())
            lat = gps.latitude
            lon = gps.longitude
            del sys.modules["adafruit_gps"]
            del adafruit_gps
            gc.collect()
            print("gps ",gc.mem_free())
            return lon,lat
        else:
            time.sleep(.1)
            if time.monotonic() - start > 10.0:
               print("no gps fix...")
               print("gps ",gc.mem_free())
               del sys.modules["adafruit_gps"]
               del adafruit_gps
               gc.collect()
               print("gps ",gc.mem_free())
               return 0.0,0.0
def lora(packet_date):
    gc.collect()
    print("lora ",gc.mem_free())
    import adafruit_rfm9x
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    #with digitalio.DigitalInOut(board.RFM9X_CS) as cs:
    rfm9x = adafruit_rfm9x.RFM9x(spi, radio_cs, radio_reset, 915.0)
    # putem ajusta putere de transmisie (in dB).  standard e de 13 dB
    #  RFM95 poate ajunge la o putere de peste 23 dB:
    rfm9x.tx_power = 20
    rfm9x.send(packet_date)
    print("lora ",gc.mem_free())
    spi.deinit()
    del sys.modules["adafruit_rfm9x"]
    del adafruit_rfm9x
    gc.collect()
    print("lora ",gc.mem_free())
 
def readbme680():
    gc.collect()
    print("bme680 ",gc.mem_free())
    import adafruit_bme680
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(board.I2C(), debug=False)

    #setam presiunea atmosferica la nivelul marii
    bme680.sea_level_pressure = 1013.25 #hPa
    print("bme680 ",gc.mem_free())
    del sys.modules["adafruit_bme680"]
    del adafruit_bme680
    gc.collect()
    print("bme280 ",gc.mem_free())
    return bme680.temperature, bme680.relative_humidity, bme680.pressure
    
def get_battery_voltage():
    return ((voltage_pin.value * 3.3) / 65536) * 2


def storedata(t,h,p,lat,lon,v):
    gc.collect()
    print("sd ",gc.mem_free())
    import adafruit_sdcard
    import storage
    radio_cs.value = True
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    sdcard = adafruit_sdcard.SDCard(spi, sd_cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    with open("/sd/temperature.txt", "a") as f:
        f.write("%0.1f %0.1f %0.1f %0.6f %0.6f %0.3f\n" % (t,h,p,lat,lon,v))
    print("data written")
    storage.umount(vfs)
    print("sd ",gc.mem_free())
    spi.deinit()
    del sys.modules["adafruit_sdcard"]
    del adafruit_sdcard
    gc.collect()
    print("sd ",gc.mem_free())

while True:
    lon, lat = get_gps_position()
    temperature, humidity, pressure=readbme680() 
    v_bat = get_battery_voltage()
    msg = bytes('{%.6f,%.6f,%0.3f,%0.2f,%0.2f,%0.2f}' % (lat, lon, v_bat,temperature,humidity,pressure), "ASCII")
    lora(msg)
    print("sending: %s" % msg)
    storedata(temperature,humidity,pressure,lat,lon,v_bat)
    print("end: ",gc.mem_free())
    gc.collect()
    print("end: ",gc.mem_free())
    print("sleeping %s seconds before restart..." % SLEEP_SECONDS)
    time.sleep(SLEEP_SECONDS)

