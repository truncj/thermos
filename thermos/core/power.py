import time
from thermos.drivers.gpio import Relay
from thermos.utils.logging import get_logger

logger = get_logger(__name__)

class SensorPower:
    """Manages power for sensors via a VCC pin."""
    
    def __init__(self, pin: int):
        self._relay = Relay(pin)
        self.pin = pin
        self._relay.on() # Default to ON
        logger.info(f"Sensor Power initialized on pin {pin}")

    def cycle(self):
        """Cycles power to the sensors."""
        logger.warning("Power cycling sensors...")
        self._relay.off()
        time.sleep(1)
        self._relay.on()
        logger.info("Sensor power restored.")
