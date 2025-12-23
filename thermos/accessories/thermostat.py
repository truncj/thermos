from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_THERMOSTAT

from thermos.core.controller import ThermostatController
from thermos.config.loader import ThermostatConfig
from thermos.utils.logging import get_logger
from thermos.utils.metrics import (
    current_temp_gauge, 
    target_temp_gauge, 
    heat_status_gauge, 
    response_time_gauge
)

logger = get_logger(__name__)

class ThermostatAccessory(Accessory):
    """
    HomeKit Accessory wrapper for the ThermostatController.
    """
    category = CATEGORY_THERMOSTAT

    def __init__(self, driver, config: ThermostatConfig, sensor_power=None):
        super().__init__(driver, display_name=config.name)
        self.controller = ThermostatController(config, sensor_power)
        
        # HAP Service Setup
        service = self.add_preload_service('Thermostat')
        
        self.char_current_temp = service.get_characteristic('CurrentTemperature')
        self.char_target_temp = service.get_characteristic('TargetTemperature')
        # Restrict valid values to 0 (Off) and 1 (Heat)
        self.char_target_state = service.get_characteristic('TargetHeatingCoolingState')
        self.char_target_state.override_properties(valid_values=[0, 1])
        self.char_current_state = service.get_characteristic('CurrentHeatingCoolingState')
        
        # Configure Config (1 = Fahrenheit)
        service.configure_char('TemperatureDisplayUnits', value=1) 
        
        # Callbacks
        self.char_target_temp.setter_callback = self._on_target_temp_changed
        self.char_target_state.setter_callback = self._on_target_state_changed
        
        # Initialize values from controller
        self._refresh_chars()

    def _refresh_chars(self):
        """Updates HAP characteristics from controller state."""
        # Convert internal state to HAP values
        self.char_target_temp.set_value(self.controller.get_target_temp())
        self.char_target_state.set_value(self.controller.get_target_state())
        
        # Mirror current state from relay status
        if self.controller.relay.is_on():
             self.char_current_state.set_value(1)
        else:
             self.char_current_state.set_value(0)
             
        # Update temp
        self.char_current_temp.set_value(self.controller.get_current_temp())


    def _on_target_temp_changed(self, value):
        logger.info(f"{self.display_name}: HAP set temp to {value}")
        self.controller.set_target_temp(value)
        self.controller.update()
        self._refresh_chars()

    def _on_target_state_changed(self, value):
        logger.info(f"{self.display_name}: HAP set state to {value}")
        self.controller.set_target_state(value)
        self.controller.update()
        self._refresh_chars()

    @Accessory.run_at_interval(3)
    async def run(self):
        """Main loop called by HAP driver."""
        try:
            self.controller.update()
            
            # Update Prometheus Metrics
            # Note: The original code exported in Fahrenheit, so we'll match that.
            ct_c = self.controller.get_current_temp()
            ct_f = (ct_c * 9/5) + 32
            
            tt_c = self.controller.get_target_temp()
            tt_f = (tt_c * 9/5) + 32
            
            # Heat status: 1 if ON, 0 if OFF
            is_heating = 1 if self.controller.relay.is_on() else 0
            heat_status_label = 1 if self.controller.get_target_state() == 1 else 0 # 1=Heat, 0=Off
            
            current_temp_gauge.labels(room=self.display_name, heat_status=heat_status_label).set(ct_f)
            target_temp_gauge.labels(room=self.display_name, heat_status=heat_status_label).set(tt_f)
            heat_status_gauge.labels(room=self.display_name).set(is_heating)
            response_time_gauge.labels(room=self.display_name).set(self.controller.last_read_duration)

            self._refresh_chars()
        except Exception as e:
            logger.error(f"Error in main loop for {self.display_name}: {e}")

    def stop(self):
        logger.info(f"Stopping {self.display_name}")
        self.controller.relay.off()
        self.controller.relay.cleanup()
