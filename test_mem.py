import sys
import digitalio
import analogio
import busio
import time
import board
import gc

voltage_pin = analogio.AnalogIn(board.D9)
radio_cs = digitalio.DigitalInOut(board.RFM9X_CS)
radio_cs.switch_to_output(True)
radio_reset = digitalio.DigitalInOut(board.RFM9X_RST)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)



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
            print("gps: ",gc.mem_free())
            #uart.deinit()
            del sys.modules["adafruit_gps"]
            gc.collect()
            print("gps: ",gc.mem_free())
            return gps.longitude, gps.latitude
        else:
            print("waiting for fix...")
            time.sleep(1)
            if time.monotonic() - start > 10.0:
               print("gps: ",gc.mem_free())
               #uart.deinit()
               del sys.modules["adafruit_gps"]
               gc.collect()
               #print("gps: ",gc.mem_free())
               print("gps: ",gc.mem_free())
               return 0.0,0.0

def lora(packet_date):
    gc.collect()
    import adafruit_rfm9x
    rfm9x = adafruit_rfm9x.RFM9x(spi, radio_cs, radio_reset, 915.0)
    rfm9x.tx_power = 20
    rfm9x.send(packet_date)
    print("lora: ",gc.mem_free())
    del sys.modules["adafruit_rfm9x"]
    gc.collect()
    print("lora: ",gc.mem_free())

def readbme680():
    gc.collect()
    import adafruit_bme680
    bme680=adafruit_bme680.Adafruit_BME680_I2C(board.I2C(), debug=False)
    bme680.sea_level_pressure = 1013.25 #hPa
    print("read_bme680: ",gc.mem_free())
    del sys.modules["adafruit_bme680"]
    gc.collect()
    print("read_bme680: ",gc.mem_free())
    return bme680.temperature, bme680.relative_humidity, bme680.pressure

def get_battery_voltage():
    return ((voltage_pin.value * 3.3) / 65536) * 2



while True:
    temperature, humidity, pressure=readbme680()
    lon, lat = get_gps_position()
    v_bat = get_battery_voltage()
    msg = bytes('{%.6f,%.6f,%s,%0.2f,%0.2f,%0.2f}' % (lat, lon, v_bat,temperature,humidity,pressure), "ASCII")
    lora(msg)
    print("sending: %s" % msg)
    time.sleep(1)
    #print("sleeping %s seconds before reset..." % "SLEEP_SECONDS")
    time.sleep(15)
    print("end of loop: ",gc.mem_free())

