"""
Receive packets over radio using RFM69 and if they fit certain form,
replay their content to a MQTT topic to specified MQTT broker.

Assumes Adafruit Feather ESP32 V2 and certain wiring of 433 MHz Radio FeatherWing.
"""

import json
import struct
import sys
import time
import traceback

import adafruit_logging as logging
import adafruit_rfm69
import board
import busio
import digitalio
import microcontroller

# pylint: disable=import-error
import socketpool

# pylint: disable=import-error
import supervisor
import wifi

from logutil import get_log_level
from mqtt import mqtt_client_setup
from mqtt_handler import MQTTHandler

try:
    from secrets import secrets
except ImportError:
    print(
        "WiFi credentials and configuration are kept in secrets.py, please add them there!"
    )
    raise


BROKER_PORT = "broker_port"
LOG_TOPIC = "log_topic"
BROKER = "broker"
PASSWORD = "password"
SSID = "ssid"
LOG_LEVEL = "log_level"
ENCRYPTION_KEY = "encryption_key"
ALLOWED_TOPICS = "allowed_topics"


def blink(pixel):
    """
    Blink the Neo pixel blue.
    """
    pixel.brightness = 0.3
    pixel.fill((0, 0, 255))
    time.sleep(0.5)
    pixel.brightness = 0


def bail(message):
    """
    Print message and exit with code 1.
    """
    print(message)
    sys.exit(1)


def check_string(name, mandatory=True):
    """
    Check is string with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, str):
        bail(f"not a string value for {name}: {value}")


def check_int(name, mandatory=True):
    """
    Check is integer with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, int):
        bail(f"not a integer value for {name}: {value}")


def check_list(name, subtype, mandatory=True):
    """
    Check whether list with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, list):
        bail(f"not a integer value for {name}: {value}")

    for item in value:
        if item and not isinstance(item, subtype):
            bail(f"not a {subtype}: {item}")


def check_bytes(name, length, mandatory=True):
    """
    Check is bytes with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, bytes):
        bail(f"not a byte value for {name}: {value}")

    if value and len(value) != length:
        bail(f"not correct length for {name}: {len(value)} should be {length}")


def check_tunables():
    """
    Check that tunables are present and of correct type.
    Will exit the program on error.
    """
    check_string(LOG_LEVEL)

    # Even though different transport can be selected than WiFi, the related tunables
    # are still mandatory, because at this point it is known which will be selected.
    # Also, MQTT topic is used for all transports.
    check_string(SSID)
    check_string(PASSWORD)
    check_string(BROKER)
    check_string(LOG_TOPIC, mandatory=False)

    check_int(BROKER_PORT)
    broker_port = secrets.get(BROKER_PORT)
    if broker_port < 0 or broker_port > 65535:
        bail(f"invalid {BROKER_PORT} value: {broker_port}")

    check_list(ALLOWED_TOPICS, str)


# pylint: disable=too-many-locals,too-many-statements
def main():
    """
    main loop: collect messages via radio, decode and publish to MQTT
    """

    check_tunables()

    log_level = get_log_level(secrets[LOG_LEVEL])
    logger = logging.getLogger("")
    logger.setLevel(log_level)

    logger.info("Running")

    # Assumes certain wiring of the Radio FeatherWing.
    cs = digitalio.DigitalInOut(board.D14)
    reset = digitalio.DigitalInOut(board.D32)

    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    rfm69 = adafruit_rfm69.RFM69(spi, cs, reset, 433)  # Europe

    encryption_key = secrets.get(ENCRYPTION_KEY)
    if encryption_key:
        logger.debug("Setting encryption key")
        rfm69.encryption_key = encryption_key

    mqtt_client = get_mqtt_client()

    logger.debug(f"allowed topics: {secrets.get(ALLOWED_TOPICS)}")

    logger.info(f"Temperature: {rfm69.temperature}C")
    logger.info(f"Frequency: {rfm69.frequency_mhz}mhz")
    logger.info(f"Bit rate: {rfm69.bitrate / 1000}kbit/s")
    logger.info(f"Frequency deviation: {rfm69.frequency_deviation}hz")

    # Wait to receive packets.  Note that this library can't receive data at a fast
    # rate, in fact it can only receive and process one 60 byte packet at a time.
    # This means you should only use this for low bandwidth scenarios, like sending
    # and receiving a single message at a time.
    logger.info("Waiting for packets...")
    while True:
        mqtt_client.loop(1)

        packet = rfm69.receive(timeout=0.1)
        if packet is None:
            continue

        logger.debug(f"Received ({len(packet)} bytes): {packet}")

        mqtt_prefix = "MQTT:"
        max_mqtt_topic_len = 36
        fmt = f">{len(mqtt_prefix)}s{max_mqtt_topic_len}sffIf"
        if struct.calcsize(fmt) > 60:
            logger.warning("the format for structure packing is bigger than 60 bytes")
        data = struct.unpack(fmt, packet)
        if len(data) != 6:
            logger.warning(f"invalid data: {data}")
            continue
        prefix = data[0].decode("ascii")
        if prefix != mqtt_prefix:
            logger.warning(f"not a MQTT prefix: {prefix}")
            continue

        mqtt_topic = data[1].decode("ascii")
        nul_idx = mqtt_topic.find("\x00")
        if nul_idx > 0:
            mqtt_topic = mqtt_topic[:nul_idx]
        logger.debug(f"MQTT topic: {mqtt_topic}")
        if mqtt_topic not in secrets.get(ALLOWED_TOPICS):
            logger.warning(f"not allowed topic: '{mqtt_topic}'")
            continue

        data = data[2:]
        pub_data_dict = {
            "humidity": data[0],
            "temperature": data[1],
            "co2_ppm": data[2],
            "battery_level": data[3],
        }
        try:
            pub_data = json.dumps(pub_data_dict)
        except TypeError:
            logger.warning(f"failed to convert to JSON: {pub_data_dict}")
            continue

        logger.info(f"Publishing to {mqtt_topic}: {pub_data}")
        mqtt_client.publish(mqtt_topic, pub_data)


def get_mqtt_client():
    """
    Connect to Wi-Fi and initialize MQTT client
    """
    logger = logging.getLogger("")

    logger.info("Connecting to wifi")
    wifi.radio.connect(secrets[SSID], secrets[PASSWORD], timeout=10)
    logger.info(f"Connected to {secrets['ssid']}")
    logger.debug(f"IP: {wifi.radio.ipv4_address}")

    pool = socketpool.SocketPool(wifi.radio)  # pylint: disable=no-member

    broker_addr = secrets[BROKER]
    broker_port = secrets[BROKER_PORT]
    mqtt_client = mqtt_client_setup(
        pool, broker_addr, broker_port, logger.getEffectiveLevel()
    )

    try:
        log_topic = secrets[LOG_TOPIC]
        # Log both to the console and via MQTT messages.
        # Up to now the logger was using the default (built-in) handler,
        # now it is necessary to add the Stream handler explicitly as
        # with a non-default handler set only the non-default handlers will be used.
        logger.addHandler(logging.StreamHandler())
        logger.addHandler(MQTTHandler(mqtt_client, log_topic))
    except KeyError:
        pass

    logger.info(f"Attempting to connect to MQTT broker {broker_addr}:{broker_port}")
    mqtt_client.connect()

    return mqtt_client


def hard_reset(exception):
    """
    Sometimes soft reset is not enough. Perform hard reset.
    """
    print(f"Got exception: {exception}")
    reset_time = 15
    print(f"Performing hard reset in {reset_time} seconds")
    time.sleep(reset_time)
    microcontroller.reset()  # pylint: disable=no-member


try:
    main()
except ConnectionError as e:
    # When this happens, it usually means that the microcontroller's wifi/networking is botched.
    # The only way to recover is to perform hard reset.
    hard_reset(e)
except MemoryError as e:
    # This is usually the case of delayed exception from the 'import wifi' statement,
    # possibly caused by a bug (resource leak) in CircuitPython that manifests
    # after a sequence of ConnectionError exceptions thrown from withing the wifi module.
    # Should not happen given the above 'except ConnectionError',
    # however adding that here just in case.
    hard_reset(e)
except Exception as e:  # pylint: disable=broad-except
    # This assumes that such exceptions are quite rare.
    # Otherwise, this would drain the battery quickly by restarting
    # over and over in a quick succession.
    print("Code stopped by unhandled exception:")
    print(traceback.format_exception(None, e, e.__traceback__))
    RELOAD_TIME = 10
    print(f"Performing a supervisor reload in {RELOAD_TIME} seconds")
    time.sleep(RELOAD_TIME)
    supervisor.reload()
