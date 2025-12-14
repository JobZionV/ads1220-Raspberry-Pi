import spidev
import gpiod
import time
from datetime import datetime

DRDY_PIN = 22

GPIO_CHIP = "/dev/gpiochip4"

SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED_HZ = 1000000

CMD_RESET = 0x06
CMD_START = 0x08
CMD_POWERDOWN = 0x02
CMD_RDATA = 0x10
CMD_WREG = 0x40
CMD_RREG = 0x20

REG_CONF0 = 0x00
REG_CONF1 = 0x01
REG_CONF2 = 0x02
REG_CONF3 = 0x03

reg0 = 0b00000000
reg1 = 0b00001100
reg2 = 0b00010000
reg3 = 0b00000000

VREF = 2.048
FSR = (2**23)

def wait_drdy(request):
    cpt = 0
    while request.get_value(DRDY_PIN):
        time.sleep(0.001)
        cpt += 1
        if cpt % 1000 == 0:
            print(f"[DEBUG] Still waiting for DRDY ({cpt} ms)")

def ads1220_write_reg(spi, reg, value):
    cmd = CMD_WREG | (reg << 2) | 0x00
    spi.xfer2([cmd, value])
    time.sleep(0.001)

def ads1220_read_reg(spi, reg):
    cmd = CMD_RREG | (reg << 2) | 0x00 
    resp = spi.xfer2([cmd, 0x00])
    return resp[1]

def ads1220_read_data(spi):
    resp = spi.xfer2([CMD_RDATA, 0x00, 0x00, 0x00])
    raw = (resp[1] << 16) | (resp[2] << 8) | resp[3]
    if raw & 0x800000:
        raw -= 1 << 24
    return raw

def ads1220_init(spi, gain):
    print("[DEBUG] Sending reset command")
    spi.xfer2([CMD_RESET])
    time.sleep(0.1)
    
    test_reg = ads1220_read_reg(spi, REG_CONF0)
    print(f"[DEBUG] REG0 before config (should be 0x00): 0x{test_reg:02X}")
    
    if test_reg == 0xFF:
        print("[WARNING] Device may not be responding - all bits read as 1")
        print("[WARNING] Check SPI connections, chip select, and power")


    print(f"[DEBUG] Writing REG0=0x{reg0:02X}, REG1=0x{reg1:02X}, REG2=0x{reg2:02X}, REG3=0x{reg3:02X}")
    ads1220_write_reg(spi, REG_CONF0, reg0)
    ads1220_write_reg(spi, REG_CONF1, reg1)
    ads1220_write_reg(spi, REG_CONF2, reg2)
    ads1220_write_reg(spi, REG_CONF3, reg3)
    
    print("[DEBUG] Verifying register writes:")
    reg0_read = ads1220_read_reg(spi, REG_CONF0)
    reg1_read = ads1220_read_reg(spi, REG_CONF1)
    reg2_read = ads1220_read_reg(spi, REG_CONF2)
    reg3_read = ads1220_read_reg(spi, REG_CONF3)
    
    print(f"[DEBUG] REG0 readback: 0x{reg0_read:02X} (expected 0x{reg0:02X})")
    print(f"[DEBUG] REG1 readback: 0x{reg1_read:02X} (expected 0x{reg1:02X})")
    print(f"[DEBUG] REG2 readback: 0x{reg2_read:02X} (expected 0x{reg2:02X})")
    print(f"[DEBUG] REG3 readback: 0x{reg3_read:02X} (expected 0x{reg3:02X})")

def raw_to_voltage(raw):
    v = (raw / float(FSR)) * (VREF)
    return v


def get_timestamp():
    return datetime.now().strftime("%d/%m/%y - %H:%M:%S")

def main():
    print("[DEBUG] GPIO initialization")
    
    request = gpiod.request_lines(
        GPIO_CHIP,
        consumer="ads1220",
        config={
            DRDY_PIN: gpiod.LineSettings(
                direction=gpiod.line.Direction.INPUT
            )
        }
    )

    gain = 1

    print(f"[DEBUG] SPI initialization (bus={SPI_BUS}, device={SPI_DEVICE}, speed={SPI_SPEED_HZ} Hz)")
    spi = spidev.SpiDev()
    
    try:
        spi.open(SPI_BUS, SPI_DEVICE)
        spi.max_speed_hz = SPI_SPEED_HZ
        spi.mode = 1
    except Exception as e:
        print(f"[ERROR] Failed to open SPI: {e}")
        request.release()
        raise

    ads1220_init(spi, gain)

    try:
        while True:
            spi.xfer2([CMD_START])
            wait_drdy(request)
            value_raw = ads1220_read_data(spi)
            value_volts = raw_to_voltage(value_raw)
            value_volts += 0.00224 # Calibration offset
            timestamp = get_timestamp()
            print(f"{timestamp} ; {value_raw:0b} ; {value_volts:.6f} ; {gain}")
            time.sleep(1)
    finally:
        print("[DEBUG] Closing SPI and releasing GPIO")
        spi.close()
        request.release()

if __name__ == '__main__':
    main()
