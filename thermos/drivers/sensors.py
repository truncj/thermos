import abc
import time
import requests
from typing import Optional
try:
    from w1thermsensor import W1ThermSensor, NoSensorFoundError
except ImportError:
    # Mock for validation on non-pi
    class W1ThermSensor:
        def get_available_sensors(self): return []
    class NoSensorFoundError(Exception): pass

from thermos.utils.logging import get_logger

logger = get_logger(__name__)

class TemperatureSensor(abc.ABC):
    """Abstract base class for temperature sensors."""

    @abc.abstractmethod
    def get_temperature(self) -> float:
        """Returns the temperature in Celsius."""
        pass
    
    @abc.abstractmethod
    def get_id(self) -> str:
        pass


class W1Sensor(TemperatureSensor):
    """Reads from a local DS18B20 sensor."""

    def __init__(self, sensor_id: str):
        self.sensor_id = sensor_id
        self._sensor = self._find_sensor(sensor_id)

    def _find_sensor(self, sensor_id: str):
        try:
            for s in W1ThermSensor.get_available_sensors():
                if s.id == sensor_id:
                    return s
        except NoSensorFoundError:
            pass
        logger.warning(f"Sensor {sensor_id} not found immediately.")
        # We might want to retry or lazy load, but for now let's return None or a dummy 
        # wrapper that tries to re-acquire.
        # implementation choice: Just try to get specific sensor by ID if library allows 
        # or wait for first read.
        return None

    def get_id(self) -> str:
        return self.sensor_id

    def get_temperature(self) -> float:
        if not self._sensor:
             # Try to re-acquire
             self._sensor = self._find_sensor(self.sensor_id)
        
        if self._sensor:
            try:
                return self._sensor.get_temperature()
            except Exception as e:
                logger.error(f"Error reading local sensor {self.sensor_id}: {e}")
                raise
        else:
            raise Exception(f"Sensor {self.sensor_id} not available")


class RemoteSensor(TemperatureSensor):
    """Reads from a remote HTTP sensor."""

    def __init__(self, url: str, fallback_sensor: Optional[TemperatureSensor] = None):
        self.url = url
        self.fallback = fallback_sensor

    def get_id(self) -> str:
        return f"REMOTE_{self.url}"

    def get_temperature(self) -> float:
        try:
            resp = requests.get(self.url, timeout=3)
            resp.raise_for_status()
            return resp.json()['temp_c']
        except requests.RequestException as e:
            logger.warning(f"Remote sensor {self.url} failed: {e}")
            if self.fallback:
                logger.info("Using fallback sensor.")
                return self.fallback.get_temperature()
            raise e
