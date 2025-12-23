import signal
import sys
from pathlib import Path

from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
from prometheus_client import start_http_server

from thermos.utils.logging import setup_logging, get_logger
from thermos.config.loader import load_config
from thermos.accessories.thermostat import ThermostatAccessory

try:
    from RPi import GPIO
except ImportError:
    # Mock GPIO for non-RPi environments
    from unittest.mock import MagicMock
    GPIO = MagicMock()
    GPIO.BCM = 11
    GPIO.OUT = 0
    GPIO.IN = 1
    GPIO.HIGH = 1
    GPIO.LOW = 0

from thermos.core.power import SensorPower

def main():
    setup_logging()
    logger = get_logger("main")
    
    # Load Configuration
    config_path = Path('./config/config.json')
    try:
        system_config, configs = load_config(config_path)
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Setup Sensor Power
    vcc_pin = system_config.vcc_pin
    sensor_power = None
    try:
        sensor_power = SensorPower(vcc_pin)
    except Exception as e:
        logger.error(f"Failed to setup VCC pin: {e}")

    # Start Prometheus Metrics
    start_http_server(8080)
    logger.info("Prometheus server started on port 8080")

    # Start HAP Driver
    driver = AccessoryDriver(port=51826, persist_file='./config/accessory.state')
    
    # Create Bridge
    bridge = Bridge(driver, 'Bridge')
    
    # Create and Add Accessories
    for name, config in configs.items():
        try:
            accessory = ThermostatAccessory(driver, config, sensor_power)
            bridge.add_accessory(accessory)
            logger.info(f"Added accessory: {name}")
        except Exception as e:
            logger.error(f"Failed to initialize accessory {name}: {e}")

    driver.add_accessory(accessory=bridge)

    # Signal Handling
    signal.signal(signal.SIGTERM, driver.signal_handler)
    
    logger.info("Starting Accessory Driver")
    driver.start()

if __name__ == "__main__":
    main()
