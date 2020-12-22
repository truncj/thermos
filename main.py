"""An example of how to setup and start an Accessory.
This is:
1. Create the Accessory object you want.
2. Add it to an AccessoryDriver, which will advertise it on the local network,
    setup a server to answer client queries, etc.
"""
import logging
import signal

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver

from devices import TemperatureSensor
from devices import Thermostat

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")


# class TemperatureSensor(Accessory):
#     """Fake Temperature sensor, measuring every 3 seconds."""
#
#     category = CATEGORY_SENSOR
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         serv_temp = self.add_preload_service('TemperatureSensor')
#         self.char_temp = serv_temp.configure_char('CurrentTemperature')
#
#     @Accessory.run_at_interval(3)
#     async def run(self):
#         self.char_temp.set_value(random.randint(18, 26))


def get_bridge(driver):
    """Call this method to get a Bridge instead of a standalone accessory."""
    bridge = Bridge(driver, 'Bridge')
    # temp_sensor = TemperatureSensor(driver, 'Sensor 2')
    # temp_sensor2 = TemperatureSensor(driver, 'Sensor 1')
    # bridge.add_accessory(temp_sensor)
    # bridge.add_accessory(temp_sensor2)

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


# Start the accessory on port 51826
driver = AccessoryDriver(port=51826)

# Change `get_accessory` to `get_bridge` if you want to run a Bridge.
driver.add_accessory(accessory=get_bridge(driver))

# We want SIGTERM (terminate) to be handled by the driver itself,
# so that it can gracefully stop the accessory, server and advertising.
signal.signal(signal.SIGTERM, driver.signal_handler)

# Start it!
driver.start()
