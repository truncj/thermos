import json
import time
import redis
from dataclasses import asdict
from typing import Dict, Any

from thermos.config.loader import ThermostatConfig
from thermos.drivers.gpio import Relay
from thermos.drivers.sensors import TemperatureSensor, W1Sensor, RemoteSensor
from thermos.core.power import SensorPower
from thermos.utils.logging import get_logger

logger = get_logger(__name__)

class ThermostatController:
    """
    Manages the core logic of a single thermostat.
    Handles reading temperature, managing target state (heat/off),
    and switching the relay.
    """
    def __init__(self, config: ThermostatConfig, sensor_power: SensorPower = None):
        self.config = config
        self.relay = Relay(config.relay_pin)
        self.sensor_power = sensor_power
        self.last_known_temp = 20.0 # Default safe value until first read
        self.last_read_duration = 0.0
        
        # Initialize Sensor
        local_sensor = W1Sensor(config.temp_id)
        if config.extra_sensor_url:
            self.sensor = RemoteSensor(config.extra_sensor_url, fallback_sensor=local_sensor)
        else:
            self.sensor = local_sensor
            
        # Redis for persistence
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self._load_state()
        
        # State tracking
        self.prev_status = ''

    def _load_state(self):
        """Loads state from Redis or initializes defaults."""
        if not self.r.exists(self.config.name):
            initial_state = {
                'target_temp': 70.0,
                'target_state': 0  # 0 = Off, 1 = Heat
            }
            self.r.set(self.config.name, json.dumps(initial_state))
            self.state = initial_state
        else:
            self.state = json.loads(self.r.get(self.config.name))
            
        # Ensure keys exist
        if 'target_temp' not in self.state:
            self.state['target_temp'] = 70.0
        if 'target_state' not in self.state:
            self.state['target_state'] = 0
            
        self._save_state()

    def _save_state(self):
        """Saves current state to Redis."""
        self.r.set(self.config.name, json.dumps(self.state))

    def set_target_temp(self, temp: float):
        self.state['target_temp'] = temp
        self._save_state()
        logger.info(f"{self.config.name}: Target Temp set to {temp}")

    def get_target_temp(self) -> float:
        return self.state['target_temp']

    def set_target_state(self, state: int):
        self.state['target_state'] = state
        self._save_state()
        logger.info(f"{self.config.name}: Target State set to {state}")

    def get_target_state(self) -> int:
        return self.state['target_state']

    def get_current_temp(self) -> float:
        try:
            start_time = time.time()
            temp_c = self.sensor.get_temperature()
            self.last_read_duration = time.time() - start_time
            
            # Simple validation to filter out bad sensor reads
            if temp_c > 37 or temp_c < 0:
                logger.error(f"{self.config.name}: Temperature out of range {temp_c}")
                if self.sensor_power:
                    self.sensor_power.cycle()
                return self.last_known_temp 
            
            self.last_known_temp = temp_c
            return temp_c
        except Exception as e:
            logger.error(f"{self.config.name}: Failed to read temperature: {e}")
            return self.last_known_temp

    def update(self) -> str:
        """
        Main control loop step. 
        Reads temp, checks thresholds, toggles relay.
        Returns a status string.
        """
        current_temp = self.get_current_temp()
        target_temp = self.get_target_temp()
        mode = self.get_target_state()
        
        # Conversions for logging/logic
        current_temp_f = (current_temp * 9/5) + 32
        
        status = ''
        
        if mode == 1: # Heat
            diff = current_temp_f - target_temp
            
            if self.relay.is_on():
                if diff >= 0.5:
                    status = 'HEAT ON - TURNING OFF (Above Threshold)'
                    self.relay.off()
                else:
                    status = 'HEAT ON - KEEPING ON'
            else:
                if diff <= -0.5:
                    status = 'HEAT OFF - TURNING ON (Below Threshold)'
                    self.relay.on()
                else:
                    status = 'HEAT OFF - KEEPING OFF'
                    
        else:
            status = 'HEAT OFF - NOT REQUESTED'
            if self.relay.is_on():
                self.relay.off()

        # Log only on status change
        if status != self.prev_status:
            logger.info(f"{self.config.name}: {status} (Curr: {current_temp_f:.1f}F, Tgt: {target_temp:.1f}F)")
            self.prev_status = status
            
        return status
