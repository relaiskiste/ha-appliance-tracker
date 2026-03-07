"""Constants for the Appliance Tracker integration."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

DOMAIN: Final = "appliance_tracker"
MANUFACTURER: Final = "Appliance Tracker"

# Config keys
CONF_APPLIANCE_NAME: Final = "appliance_name"
CONF_APPLIANCE_TYPE: Final = "appliance_type"
CONF_POWER_SENSOR: Final = "power_sensor"
CONF_START_THRESHOLD: Final = "start_threshold"
CONF_STOP_THRESHOLD: Final = "stop_threshold"
CONF_START_DELAY: Final = "start_delay"
CONF_STOP_DELAY: Final = "stop_delay"
CONF_FINISHING_DELAY: Final = "finishing_delay"
CONF_COMPLETE_TIMEOUT: Final = "complete_timeout"

# Defaults
DEFAULT_START_DELAY: Final = 30  # seconds
DEFAULT_STOP_DELAY: Final = 60  # seconds
DEFAULT_FINISHING_DELAY: Final = 180  # seconds (3 min)
DEFAULT_COMPLETE_TIMEOUT: Final = 300  # seconds (5 min)


class ApplianceType(StrEnum):
    """Supported appliance types."""

    WASHING_MACHINE = "washing_machine"
    DRYER = "dryer"
    DISHWASHER = "dishwasher"
    CUSTOM = "custom"


class ApplianceState(StrEnum):
    """Appliance cycle states."""

    IDLE = "idle"
    RUNNING = "running"
    FINISHING = "finishing"
    COMPLETE = "complete"


# Default thresholds per appliance type (start_watts, stop_watts)
DEFAULT_THRESHOLDS: Final[dict[str, tuple[float, float]]] = {
    ApplianceType.WASHING_MACHINE: (10.0, 5.0),
    ApplianceType.DRYER: (50.0, 10.0),
    ApplianceType.DISHWASHER: (10.0, 5.0),
    ApplianceType.CUSTOM: (10.0, 5.0),
}

# Attributes
ATTR_CYCLE_START: Final = "cycle_start"
ATTR_CYCLE_COUNT: Final = "cycle_count"
ATTR_LAST_CYCLE_DURATION: Final = "last_cycle_duration"
ATTR_LAST_CYCLE_ENERGY: Final = "last_cycle_energy"
ATTR_CURRENT_POWER: Final = "current_power"
ATTR_APPLIANCE_TYPE: Final = "appliance_type"
ATTR_START_THRESHOLD: Final = "start_threshold"
ATTR_STOP_THRESHOLD: Final = "stop_threshold"
