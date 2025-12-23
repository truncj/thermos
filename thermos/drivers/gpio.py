try:
    from RPi import GPIO
except ImportError:
    # Mock GPIO for non-RPi environments (like during development on Mac)
    from unittest.mock import MagicMock
    GPIO = MagicMock()
    # Define constants usually found in RPi.GPIO
    GPIO.BCM = 11
    GPIO.OUT = 0
    GPIO.IN = 1
    GPIO.HIGH = 1
    GPIO.LOW = 0
    GPIO.PUD_OFF = 0

from thermos.utils.logging import get_logger

logger = get_logger(__name__)

class Relay:
    """Controls a relay via GPIO."""

    def __init__(self, pin: int):
        self.pin = pin
        self._setup_gpio()

    def _setup_gpio(self):
        """Initializes the GPIO pin."""
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
            logger.info("GPIO mode set to BCM")
        
        GPIO.setup(self.pin, GPIO.OUT)
        # Default to OFF (Low)
        GPIO.output(self.pin, GPIO.LOW)
        logger.debug(f"Relay pin {self.pin} setup as OUTPUT")

    def on(self):
        """Turns the relay ON."""
        GPIO.output(self.pin, GPIO.HIGH)
        # logger.debug(f"Relay {self.pin} ON")

    def off(self):
        """Turns the relay OFF."""
        GPIO.output(self.pin, GPIO.LOW)
        # logger.debug(f"Relay {self.pin} OFF")

    def is_on(self) -> bool:
        """Checks if the relay is ON."""
        return GPIO.input(self.pin) == GPIO.HIGH

    def cleanup(self):
        """Cleans up the GPIO pin."""
        GPIO.cleanup(self.pin)
