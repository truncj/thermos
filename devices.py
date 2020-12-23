import json
import logging

import redis
from RPi import GPIO
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR, CATEGORY_THERMOSTAT

from w1thermsensor import W1ThermSensor


class Thermostat(Accessory):
    category = CATEGORY_THERMOSTAT  # This is for the icon in the iOS Home app.

    @classmethod
    def _gpio_setup(_cls, relay_pin, temp_pin):
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        # todo remove mock pin
        if relay_pin == 999:
            return
        GPIO.setup(relay_pin, GPIO.OUT)
        GPIO.setup(temp_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def __init__(self, *args, **kwargs):
        """Here, we just store a reference to the current temperature characteristic and
        add a method that will be executed every time its value changes.
        """
        # If overriding this method, be sure to call the super's implementation first.
        super().__init__(*args, **kwargs)

        # Add the services that this Accessory will support with add_preload_service here
        temp_service = self.add_preload_service('Thermostat')
        self.current_temp = temp_service.get_characteristic('CurrentTemperature')
        self.target_temp = temp_service.get_characteristic('TargetTemperature')
        self.target_state = temp_service.get_characteristic('TargetHeatingCoolingState')
        # self.current_state = temp_service.get_characteristic('CurrentHeatingCoolingState')

        # Default unit to Fahrenheit (change to 0 for Celcius)
        temp_service.configure_char('TemperatureDisplayUnits', value=1)

        # Having a callback is optional, but you can use it to add functionality.
        self.target_temp.setter_callback = self.target_temp_changed
        self.current_temp.setter_callback = self.current_temp_changed
        self.target_state.setter_callback = self.target_state_changed
        # self.current_state.setter_callback = self.current_state_changed

        # initialize redis connection per device
        self.r = redis.Redis(
            host='localhost',
            port=6379,
            password='',
            decode_responses=True)

        if not self.r.exists(self.display_name):
            self.r.set(self.display_name, '{}')

        state = json.loads(self.r.get(self.display_name))

        with open('config/config.json') as f:
            data = json.load(f)
            state['relay_pin'] = data[self.display_name]['relay_pin']
            state['temp_pin'] = data[self.display_name]['temp_pin']
            state['temp_id'] = data[self.display_name]['temp_id']

        # initialize gpio
        self.relay_pin = state['relay_pin']
        self.temp_pin = state['temp_pin']
        self._gpio_setup(self.relay_pin, self.temp_pin)

        # sane defaults for target temp if doesn't already exist
        state['target_temp'] = state.get('target_temp', 70)
        self.target_temp.set_value(state['target_temp'])

        # sane defaults for target state if doesn't already exist
        state['target_state'] = state.get('target_state', 0)
        self.target_state.set_value(state['target_state'])

        self.r.set(self.display_name, json.dumps(state))

    def target_state_changed(self, value):
        """This will be called every time the value of the CurrentTemperature
        is changed. Use setter_callbacks to react to user actions, e.g. setting the
        lights On could fire some GPIO code to turn on a LED (see pyhap/accessories/LightBulb.py).
        """

        # get existing target_state
        json_state = json.loads(self.r.get(self.display_name))

        # set new target_state
        json_state['target_state'] = value
        self.r.set(self.display_name, json.dumps(json_state))

        print('Target State changed to: ', value)

    def target_temp_changed(self, value):
        # self.temp_target.set_value(value)

        # get existing target_temp
        json_state = json.loads(self.r.get(self.display_name))

        # set new target_temp
        json_state['target_temp'] = value
        self.r.set(self.display_name, json.dumps(json_state))
        print('Temperature [TARGET] changed to: ', value)

    def current_temp_changed(self, value):
        """This will be called every time the value of the CurrentTemperature
        is changed. Use setter_callbacks to react to user actions, e.g. setting the
        lights On could fire some GPIO code to turn on a LED (see pyhap/accessories/LightBulb.py).
        """
        print('Temperature [CURRENT] changed to: ', value)

    @Accessory.run_at_interval(2)  # Run this method every 3 seconds
    # The `run` method can be `async` as well
    async def run(self):
        """We override this method to implement what the accessory will do when it is
        started.

        We set the current temperature to a random number. The decorator runs this method
        every 3 seconds.
        """
        sensor = W1ThermSensor()
        sensors = sensor.get_available_sensors()

        for _ in sensors:

            data = json.loads(self.r.get(self.display_name))

            # todo remove once we have more than one thermometer
            if data['temp_id'] == 'XXXXXXXXXXX':
                fake_temp = 21
                self.current_temp.set_value(fake_temp)
                # check if heat should be turned based on 0.5C threshold
                # todo remove mock pin
                if self.relay_pin == 999:
                    return
                if (self.target_temp.value - fake_temp > 0.5)\
                        and self.target_state.value == 1:
                    GPIO.output(self.relay_pin, GPIO.HIGH)
                else:
                    GPIO.output(self.relay_pin, GPIO.LOW)
            else:

                if sensor.id == data['temp_id']:
                    self.current_temp.set_value(sensor.get_temperature())

                    # check if heat should be turned based on 0.5C threshold
                    if (self.target_temp.value - sensor.get_temperature() > 0.5)\
                            and self.target_state.value == 1:
                        GPIO.output(self.relay_pin, GPIO.HIGH)
                    else:
                        GPIO.output(self.relay_pin, GPIO.LOW)

            # to fahrenheit
            d = u"\u00b0"
            cf = round(9.0/5.0 * self.current_temp.value + 32, 2)
            tf = round(9.0/5.0 * self.target_temp.value + 32, 2)

            logging.info(f'{self.display_name} (Current:{cf}{d}F Target:{tf}{d}F)')

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
        self.temp_char.set_value(20)
        # self.temp_char.set_value(random.randint(18, 26))

    # The `stop` method can be `async` as well
    def stop(self):
        """We override this method to clean up any resources or perform final actions, as
        this is called by the AccessoryDriver when the Accessory is being stopped.
        """
        print('Stopping accessory.')