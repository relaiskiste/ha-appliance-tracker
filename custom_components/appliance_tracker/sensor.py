"""Sensor platform for Appliance Tracker."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_APPLIANCE_NAME,
    CONF_APPLIANCE_TYPE,
    DOMAIN,
    MANUFACTURER,
    ApplianceState,
)
from .coordinator import ApplianceTrackerCoordinator


@dataclass(frozen=True, kw_only=True)
class ApplianceTrackerSensorDescription(SensorEntityDescription):
    """Describe an Appliance Tracker sensor."""

    value_fn: Callable[[ApplianceTrackerCoordinator], Any]
    attr_fn: Callable[[ApplianceTrackerCoordinator], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[ApplianceTrackerSensorDescription, ...] = (
    ApplianceTrackerSensorDescription(
        key="state",
        translation_key="appliance_state",
        device_class=SensorDeviceClass.ENUM,
        options=[s.value for s in ApplianceState],
        value_fn=lambda c: c.appliance_state.value,
        attr_fn=lambda c: {
            "current_power": f"{c.current_power:.1f} W",
            "start_threshold": f"{c.start_threshold} W",
            "stop_threshold": f"{c.stop_threshold} W",
            "cycle_start": c.cycle_start.isoformat() if c.cycle_start else None,
        },
    ),
    ApplianceTrackerSensorDescription(
        key="current_power",
        translation_key="current_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda c: round(c.current_power, 1),
    ),
    ApplianceTrackerSensorDescription(
        key="cycle_count",
        translation_key="cycle_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        value_fn=lambda c: c.cycle_count,
    ),
    ApplianceTrackerSensorDescription(
        key="last_cycle_duration",
        translation_key="last_cycle_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        suggested_display_precision=1,
        value_fn=lambda c: c.last_cycle_duration,
    ),
    ApplianceTrackerSensorDescription(
        key="last_cycle_energy",
        translation_key="last_cycle_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:lightning-bolt",
        suggested_display_precision=3,
        value_fn=lambda c: c.last_cycle_energy,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Appliance Tracker sensors."""
    coordinator: ApplianceTrackerCoordinator = entry.runtime_data

    async_add_entities(
        ApplianceTrackerSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class ApplianceTrackerSensor(
    CoordinatorEntity[ApplianceTrackerCoordinator], SensorEntity
):
    """Representation of an Appliance Tracker sensor."""

    entity_description: ApplianceTrackerSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ApplianceTrackerCoordinator,
        entry: ConfigEntry,
        description: ApplianceTrackerSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_APPLIANCE_NAME],
            manufacturer=MANUFACTURER,
            model=entry.data[CONF_APPLIANCE_TYPE].replace("_", " ").title(),
            entry_type=DeviceEntryType.SERVICE,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator)
        return None
