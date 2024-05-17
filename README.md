
# Radio (RFM69) to MQTT gateway

Receive messages in certain format over RFM69 based radio, decode them and publish as MQTT messages using WiFi.
The code assumes Feather ESP32 V2 and certain wiring of the Radio FeatherWing.

This is the server piece for [shield](https://github.com/vladak/shield/).

## Hardware

Here is a bill of materials:

Purpose | Name
---|---
microcontroller | [ESP32 Feather V2 with w.FL antenna connector](https://www.adafruit.com/product/5438)
WiFi antenna | [WiFi Antenna with w.FL / MHF3 / IPEX3 Connector](https://www.adafruit.com/product/5445)
radio | [Radio FeatherWing 433 MHz](https://www.adafruit.com/product/3230) 

Most of the stuff comes from [Adafruit](https://www.adafruit.com/).

## Software/firmware install

Firstly, the microcontroller needs to be converted to run CircuitPython 9.x (for the `circup` to work with web workflow). To do that, for ESP32 V2, I chose the [command line `esptool`](https://learn.adafruit.com/circuitpython-with-esp32-quick-start/command-line-esptool) on a Linux computer (since macOS appeared to have flaky serial connection for some reason), however these days it can be done using [Web Flasher](https://adafruit.github.io/Adafruit_WebSerial_ESPTool/) in Chrome. For ESP32-S2 (QtPy) this procedure is simpler.

Once CicuitPython is installed, perform the initial set up by [creating the `settings.toml` file](https://learn.adafruit.com/circuitpython-with-esp32-quick-start/setting-up-web-workflow
) in the root directory (using `screen` when the board is connected via USB data cable):
```
f = open('settings.toml', 'w')
f.write('CIRCUITPY_WIFI_SSID = "wifissid"\n')
f.write('CIRCUITPY_WIFI_PASSWORD = "wifipassword"\n')
f.write('CIRCUITPY_WEB_API_PASSWORD = "XXX"\n')
f.close()
```
and restart the microcontroller. **This should not be done for the microcontroller using the radio transmission** to keep things simple and avoid any WiFi induced problems.

Then the following can be used:
- copy `*.py` files to the root directory using web workflow, assumes system with `curl` installed:
  ```
  for f in *.py; do curl -v -u :XXX -T "$f" -L --location-trusted "http://172.40.0.11/fs/$f"; done
  ```
- create `secrets.py` in the root directory (using the same technique as in the previous step)
- install necessary libraries from Adafruit CircuitPython bundle to the `lib` directory using web workflow:
  ```
  circup --host 172.40.0.11 --password XXX install -r requirements.txt
  ```

## Configuration

There needs to be a `secrets.py` file that contains Wi-Fi credentials and MQTT configuration.
It can look like this:
```python
# This file is where you keep secret settings, passwords, and tokens!
# If you put them in the code you risk committing that info or sharing it

secrets = {
    "ssid": "foo",
    "password": "bar",
    "broker": "172.40.0.3",
    "broker_port": 1883,
    "allowed_topics": ["devices/terasa/shield"],
    "log_topic": "logs/terasa/shield",
    "log_level": "INFO",
}
```

To transfer the file to the microcontroller, the same method as in the Install section should be used.

### Tunables

Purpose | Name                                                                                                                                              | Type | Kind
---|---------------------------------------------------------------------------------------------------------------------------------------------------|---|---
`ssid` | WiFi SSID                                                                                                                                         | `str` | Mandatory
`password` | WiFi password                                                                                                                                     | `str` | Mandatory
`broker` | MQTT broker address                                                                                                                               | `str` | Mandatory
`broker_port` | MQTT broker port                                                                                                                                  | `int` | Mandatory
`allowed_topics` | MQTT topics to publish messages to                                                                                                                 | `list` of `str` | Mandatory
`log_topic` | MQTT topic to publish log messages to                                                                                                             | `str` | Optional
`log_level` | log level, default `INFO`                                                                                                                         | `str` | Mandatory
`tx_power` | TX power to use for RFM69                                                                                                                          | `int` | Optional
`encryption_key` | 16 bytes of encryption key for RFM69                                                                                                               | `bytes` | Optional

## Lessons learned

- The 433 MHz signal using 16.5 cm wire antenna can easily reach across the apartment, i.e. through brick/concrete walls and windows.

## Guide/documentation links

Adafruit has largely such a good documentation that the links are worth putting here for quick reference:
- [web workflow RESTful API](https://docs.circuitpython.org/en/latest/docs/workflows.html#file-rest-api)
- [CircuitPython RGB Status Light color coding](https://learn.adafruit.com/welcome-to-circuitpython/troubleshooting#circuitpython-rgb-status-light-2978455)
- [CircuitPython for RFM69](https://learn.adafruit.com/radio-featherwing/circuitpython-for-rfm69)
- [on RFM69 wiring to the microcontroller pins](https://forums.adafruit.com/viewtopic.php?p=886292&hilit=433#p886292)
