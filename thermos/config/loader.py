import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

@dataclass
class ThermostatConfig:
    name: str  # Display Name essentially
    relay_pin: int
    temp_pin: int
    temp_id: str
    extra_sensor_url: Optional[str] = None
    # We can add default target temps/states here later if we want config to drive defaults

@dataclass
class SystemConfig:
    vcc_pin: int = 22  # Default to 22 if not specified

def load_config(config_path: Path) -> (SystemConfig, Dict[str, ThermostatConfig]):
    """Loads the thermostat configuration from a JSON file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open('r') as f:
        data = json.load(f)

    # Check if there is a 'system' key for global settings
    system_data = data.pop('system', {})
    system_config = SystemConfig(vcc_pin=system_data.get('vcc_pin', 22))

    configs = {}
    for name, details in data.items():
        configs[name] = ThermostatConfig(
            name=name,
            relay_pin=details.get('relay_pin'),
            temp_pin=details.get('temp_pin'),
            temp_id=details.get('temp_id'),
            extra_sensor_url=details.get('extra_sensor')
        )
    return system_config, configs
