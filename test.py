import sys
import digitalio
import analogio
import busio
import time
import board
import gc
import sdcardio
import storage

voltage_pin = analogio.AnalogIn(board.D9)
radio_cs = digitalio.DigitalInOut(board.RFM9X_CS)
radio_cs.switch_to_output(True)
radio_reset = digitalio.DigitalInOut(board.RFM9X_RST)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
sdcard = sdcardio.SDCard(spi, board.D5)
#formatam cardul
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")


def get_gps_position():
    gc.collect()
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
            del(adafruit_gps)
            del(sys.modules["adafruit_gps"])
            gc.collect()
            return gps.longitude, gps.latitude
        else:
            print("waiting for fix...")
            time.sleep(0.1)
            if time.monotonic() - start > 10.0:
               del(adafruit_gps)
               del(sys.modules["adafruit_gps"])
               gc.collect()
               return 0.0,0.0
def lora(packet_date):
    gc.collect()
    import adafruit_rfm9x
    #with digitalio.DigitalInOut(board.RFM9X_CS) as cs:
    rfm9x = adafruit_rfm9x.RFM9x(spi, radio_cs, radio_reset, 915.0)
    # putem ajusta putere de transmisie (in dB).  standard e de 13 dB
    #  RFM95 poate ajunge la o putere de peste 23 dB:
    rfm9x.tx_power = 20
    rfm9x.send(packet_date)
    del(adafruit_rfm9x)
    del(sys.modules["adafruit_rfm9x"])
    gc.collect()
    
def parametrii():
    gc.collect()
    import adafruit_bme680
    bme680 = adafruit_bme680.Adafruit_BME680_I2C(board.I2C(), debug=False)

    #setam presiunea atmosferica la nivelul marii
    bme680.sea_level_pressure = 1013.25 #hPa
    del(adafruit_bme680)
    del(sys.modules["adafruit_bme680"])
    gc.collect()
    return bme680.temperature, bme680.relative_humidity, bme680.pressure
    
def get_battery_voltage():
    return ((voltage_pin.value * 3.3) / 65536) * 2

def stocare(t,h,p,lat,lon):
    # Use any pin that is not taken by SPI

    # din cauza ca modulul lora foloseste CS afecteaza -- fai si tu o formulare
    radio_cs.value=True
    # configuram SPI
    

    # Use the filesystem as normal! Our files are under /sd


    with open("/sd/temperature.txt", "a") as f:
        f.write("%0.1f\n" % t)
    print("test")
    gc.collect()
    
while True:
    #msg1 = bytes('{{%.2f,%.2f,%.2f,%.2f}}' % (tp, hu, ps,gas), "ASCII")
    lon, lat = get_gps_position()
    value1, value2, value3=parametrii() #achizitionez parametrii de mediu
    v_bat = get_battery_voltage()
    #stochez pe sdcard o parte din parametrii
    # trimit urmatorii parametrii latitudine,longitudine,vabt,temp,hu,pres,gas
    msg = bytes('{%.6f,%.6f,%s,%0.2f,%0.2f,%0.2f}' % (lat, lon, v_bat,value1,value2,value3), "ASCII")
    lora(msg)
        
    print("sending: %s" % msg)
    stocare(value1,value2,value3,0,0)
        
    time.sleep(1)
    #print(time.monotonic()) #timpul in minute de cand a pornit modulul
    print("sleeping %s seconds before reset..." % "SLEEP_SECONDS")
    time.sleep(15)
    print(gc.mem_free())
    #print("Done sleeping - resetting feather to reclaim lost RAM...")
    #import supervisor
    #supervisor.reload()

