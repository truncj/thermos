import random

from RPi import GPIO
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_THERMOSTAT


class Thermostat(Accessory):
    category = CATEGORY_THERMOSTAT  # This is for the icon in the iOS Home app.

    @classmethod
    def _gpio_setup(_cls, pin):
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)

    def __init__(self, *args, pin=23, **kwargs):
        """Here, we just store a reference to the current temperature characteristic and
        add a method that will be executed every time its value changes.
        """
        # If overriding this method, be sure to call the super's implementation first.
        super().__init__(*args, **kwargs)

        # Add the services that this Accessory will support with add_preload_service here
        temp_service = self.add_preload_service('Thermostat')
        self.temp_current = temp_service.get_characteristic('CurrentTemperature')
        self.temp_target = temp_service.get_characteristic('TargetTemperature')
        self.target_state = temp_service.get_characteristic('TargetHeatingCoolingState')
        # self.current_state = temp_service.get_characteristic('CurrentHeatingCoolingState')

        # Default unit to Fahrenheit (change to 0 for Celcius)
        temp_service.configure_char('TemperatureDisplayUnits', value=1)

        self.pin = pin

        # Having a callback is optional, but you can use it to add functionality.
        self.temp_target.setter_callback = self.temperature_target_changed
        self.temp_current.setter_callback = self.temperature_current_changed
        self.target_state.setter_callback = self.target_state_changed
        # self.current_state.setter_callback = self.current_state_changed

    def target_state_changed(self, value):
        """This will be called every time the value of the CurrentTemperature
        is changed. Use setter_callbacks to react to user actions, e.g. setting the
        lights On could fire some GPIO code to turn on a LED (see pyhap/accessories/LightBulb.py).
        """
        # if state is turned to 'OFF'
        if value == 0:
            GPIO.output(self.pin, GPIO.LOW)
        elif value == 1:
            GPIO.output(self.pin, GPIO.HIGH)
        else:
            GPIO.output(self.pin, GPIO.LOW)

        print('Target State changed to: ', value)

    # def current_state_changed(self, value):
    #   print('Current State changed to: ', value)

    def temperature_target_changed(self, value):
        """This will be called every time the value of the CurrentTemperature
        is changed. Use setter_callbacks to react to user actions, e.g. setting the
        lights On could fire some GPIO code to turn on a LED (see pyhap/accessories/LightBulb.py).
        """
        print('Temperature [TARGET] changed to: ', value)

    def temperature_current_changed(self, value):
        """This will be called every time the value of the CurrentTemperature
        is changed. Use setter_callbacks to react to user actions, e.g. setting the
        lights On could fire some GPIO code to turn on a LED (see pyhap/accessories/LightBulb.py).
        """
        print('Temperature [CURRENT] changed to: ', value)

    @Accessory.run_at_interval(3)  # Run this method every 3 seconds
    # The `run` method can be `async` as well
    def run(self):
        """We override this method to implement what the accessory will do when it is
        started.

        We set the current temperature to a random number. The decorator runs this method
        every 3 seconds.
        """
        self.temp_current.set_value(random.randint(20, 30))
        # self.temp_target.set_value(random.randint(22, 28))

    # The `stop` method can be `async` as well
    def stop(self):
        """We override this method to clean up any resources or perform final actions, as
        this is called by the AccessoryDriver when the Accessory is being stopped.
        """
        print('Stopping accessory.')


class TemperatureSensor(Accessory):
    """Implementation of a mock temperature sensor accessory."""

    category = CATEGORY_SENSOR  # This is for the icon in the iOS Home app.

    def __init__(self, *args, **kwargs):
        """Here, we just store a reference to the current temperature characteristic and
        add a method that will be executed every time its value changes.
        """
        # If overriding this method, be sure to call the super's implementation first.
        super().__init__(*args, **kwargs)

        # Add the services that this Accessory will support with add_preload_service here
        temp_service = self.add_preload_service('TemperatureSensor')
        self.temp_char = temp_service.get_characteristic('CurrentTemperature')

        # Having a callback is optional, but you can use it to add functionality.
        self.temp_char.setter_callback = self.temperature_changed

    def temperature_changed(self, value):
        """This will be called every time the value of the CurrentTemperature
        is changed. Use setter_callbacks to react to user actions, e.g. setting the
        lights On could fire some GPIO code to turn on a LED (see pyhap/accessories/LightBulb.py).
        """
        print('Temperature changed to: ', value)

    @Accessory.run_at_interval(3)  # Run this method every 3 seconds
    # The `run` method can be `async` as well
    def run(self):
        """We override this method to implement what the accessory will do when it is
        started.

        We set the current temperature to a random number. The decorator runs this method
        every 3 seconds.
        """
        self.temp_char.set_value(random.randint(18, 26))

    # The `stop` method can be `async` as well
    def stop(self):
        """We override this method to clean up any resources or perform final actions, as
        this is called by the AccessoryDriver when the Accessory is being stopped.
        """
        print('Stopping accessory.')