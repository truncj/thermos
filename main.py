"""An example of how to setup and start an Accessory.
This is:
1. Create the Accessory object you want.
2. Add it to an AccessoryDriver, which will advertise it on the local network,
    setup a server to answer client queries, etc.
"""
import logging
import signal

from prometheus_client import Gauge, start_http_server

from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver

from devices import TemperatureSensor
from devices import Thermostat

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(asctime)ss %(message)s", datefmt='%Y-%m-%d %H:%M:%S')


def get_bridge(driver):
    """Call this method to get a Bridge instead of a standalone accessory."""
    bridge = Bridge(driver, 'Bridge')

    tstat1 = Thermostat(driver, 'LivingRoom')
    tstat2 = Thermostat(driver, 'SunRoom')
    tstat3 = Thermostat(driver, 'Bedrooms')
    tstat4 = Thermostat(driver, 'MasterBedroom')
    tstat5 = Thermostat(driver, 'Downstairs')
    tstat6 = Thermostat(driver, 'DownstairsBedrooms')

    bridge.add_accessory(tstat1)
    bridge.add_accessory(tstat2)
    bridge.add_accessory(tstat3)
    bridge.add_accessory(tstat4)
    bridge.add_accessory(tstat5)
    bridge.add_accessory(tstat6)

    return bridge


def get_accessory(driver):
    """Call this method to get a standalone Accessory."""
    return TemperatureSensor(driver, 'MyTempSensor')


# Start the accessory on port 51826 & save the accessory.state to our custom path
driver = AccessoryDriver(port=51827, persist_file='./config/accessory.state')

# Change `get_accessory` to `get_bridge` if you want to run a Bridge.
driver.add_accessory(accessory=get_bridge(driver))

# We want SIGTERM (terminate) to be handled by the driver itself,
# so that it can gracefully stop the accessory, server and advertising.
signal.signal(signal.SIGTERM, driver.signal_handler)

# Expose metrics
start_http_server(8080)

# Start it!
driver.start()
