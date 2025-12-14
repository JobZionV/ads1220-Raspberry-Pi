# ADS1220 ADC Python Interface

This Python script interfaces with the **Texas Instruments ADS1220** 24-bit Analog-to-Digital Converter (ADC) using a Raspberry Pi (or compatible Linux SBC).

It utilizes hardware SPI for communication and `libgpiod` for monitoring the Data Ready (DRDY) signal.

## Features
* **SPI Communication:** Configures and controls the ADS1220 via `spidev`.
* **Register Verification:** Writes configuration registers and immediately reads them back to verify successful communication.
* **DRDY Polling:** Monitors the DRDY pin to ensure data is ready before reading.
* **Data Conversion:** Converts raw 24-bit 2's complement data into voltage readings.
* **Logging:** Prints timestamped data, binary raw values, and calculated voltage to the console.

## Hardware Requirements
* Raspberry Pi 5 (should work on other Rasperry Pi devices, but not tested)
* TI ADS1220 ADC module.
* Connections via SPI Bus 0.

### Pin Configuration
Based on the code defaults:

| ADS1220 Pin | Raspberry Pi Pin | Function |
| :--- | :--- | :--- |
| **CS** | GPIO 8 (CE0) | SPI Chip Select |
| **SCLK** | GPIO 11 (SCLK) | SPI Clock |
| **MOSI** | GPIO 10 (MOSI) | SPI Master Out |
| **MISO** | GPIO 9 (MISO) | SPI Master In |
| **DRDY** | **GPIO 22** | Data Ready Interrupt |
| **VCC/GND** | 3.3V / GND | Power |

> **Note:** The script is currently set to use `/dev/gpiochip4`. This is common on the Raspberry Pi 5. If using an older Pi (3 or 4), you may need to change this to `/dev/gpiochip0`.

## Software Prerequisites

Ensure you have Python 3 installed. You will need the `spidev` and `gpiod` libraries.

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-libgpiod
pip3 install spidev gpiod
```
*Note*: Enable SPI in your Raspberry Pi configuration (sudo raspi-config > Interface Options > SPI).

## Configuration

You can adjust the following constants at the top of the script to match your hardware setup:

* **`GPIO_CHIP`**: Path to the GPIO chip (e.g., `"/dev/gpiochip4"` or `"/dev/gpiochip0"`).
* **`DRDY_PIN`**: The GPIO pin number connected to the ADS1220 DRDY pin.
* **`SPI_SPEED_HZ`**: SPI Clock speed (Default: 1MHz).
* **`VREF`**: Reference voltage (Default: 2.048V).

### Register Settings
The script initializes the ADS1220 with the following hardcoded bitmasks:
* `reg0`: Mux settings / Gain.
* `reg1`: Data rate / Mode.
* `reg2`: Voltage Reference configuration.
* `reg3`: IDAC settings.

## Usage

Run the script using Python 3:

```bash
python3 main.py
```

### Output Format
The script prints data to the console in the following CSV-like format:
```text
DD/MM/YY - HH:MM:SS ; <Binary Raw Data> ; <Voltage> ; <Gain>
```

**Example:**
```text
15/12/25 - 10:30:01 ; 1011001010101010001 ; 1.250400 ; 1
```

## Troubleshooting
1.  **"Failed to open SPI"**: Ensure SPI is enabled in `raspi-config` and you have permission to access `/dev/spidev0.0` (usually requires the user to be in the `spi` group).
2.  **"Device may not be responding"**: Check your wiring. If `REG0` reads back as `0xFF`, the MISO line might be floating or the device is not powered.
3.  **GPIO Error**: If the script crashes on `gpiod` request, check that `GPIO_CHIP` points to the correct device for your specific Raspberry Pi model.