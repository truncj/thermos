from prometheus_client import Gauge, Counter

# Initialize prometheus metrics gauges
# We define them globally so they are registered once
current_temp_gauge = Gauge(f"current_temperature", "Temperature in F", labelnames=["room", "heat_status"])
target_temp_gauge = Gauge(f"target_temperature", "Temperature in F", labelnames=["room", "heat_status"])
heat_status_gauge = Gauge(f"heat_status", "Heat On/Off Status", labelnames=["room"])
response_time_gauge = Gauge(f"response_time", "Temp Sensor Response Time", labelnames=["room"])
