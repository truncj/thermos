import json
import logging
import requests
from datetime import datetime, timedelta


# TODO clean-up
# using weather.gov api for weather data
def get_weather(device, url):

    fmt = "%d-%m-%Y %H:%M:%S"
    now = datetime.now().strftime(fmt)

    data = {
        "weather_ts": 0,
        "outdoor_temp": 0
    }

    if not device.r.exists('_aux'):
        device.r.set('_aux', f'{json.dumps(data)}')

    aux_json = json.loads(device.r.get('_aux'))

    if aux_json['weather_ts'] == 0 or \
            datetime.strptime(now, fmt) - datetime.strptime(aux_json['weather_ts'], fmt) > timedelta(minutes=5):
        try:
            device.r.set('_aux', f'{{"weather_ts": "{now}"}}')
            # hourly forecast url from https://api.weather.gov/points/{lat},{long}
            resp = requests.get(url)
        except Exception as e:
            logging.error(f'Exception while getting weather data: {e}')
            return

        resp_json = json.loads(resp.text)
        properties = resp_json['properties']

        for period in properties['periods']:
            if period['number'] == 1:
                outdoor_temp = period['temperature']
                aux_json['outdoor_temp'] = outdoor_temp
                aux_json['weather_ts'] = now
                device.r.set('_aux', json.dumps(aux_json))

    return aux_json['outdoor_temp']

