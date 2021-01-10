import json
import logging
import requests
from datetime import datetime as dt, timedelta


# TODO clean-up
# using weather.gov api for weather data
def get_weather(device, url):

    fmt = "%d-%m-%Y %H:%M:%S"
    now = dt.now().strftime(fmt)

    if not device.r.exists('_aux'):
        device.r.set('_aux', {})

    aux_json = json.loads(device.r.get('_aux'))

    if 'weather_ts' not in aux_json or \
       'outdoor_temp' not in aux_json or \
       dt.strptime(now, fmt) - dt.strptime(aux_json['weather_ts'], fmt) > timedelta(minutes=5):

        try:
            device.r.set('_aux', f'{{"weather_ts": "{now}"}}')
            # hourly forecast url from https://api.weather.gov/points/{lat},{long}
            resp = requests.get(url)
        except Exception as e:
            logging.error(f'Exception while getting weather data: {e}')
            return

        resp_json = json.loads(resp.text)

        if 'properties' in resp_json:
            properties = resp_json['properties']
        else:
            logging.error('weather response "properties" is missing ')
            return

        for period in properties['periods']:
            if period['number'] == 1:
                outdoor_temp = period['temperature']
                aux_json['outdoor_temp'] = outdoor_temp
                aux_json['weather_ts'] = now
                device.r.set('_aux', json.dumps(aux_json))

    return aux_json['outdoor_temp']

