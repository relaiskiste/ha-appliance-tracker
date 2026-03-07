"""Binary sensor platform for Appliance Tracker."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_APPLIANCE_NAME, CONF_APPLIANCE_TYPE, DOMAIN, MANUFACTURER
from .coordinator import ApplianceTrackerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Appliance Tracker binary sensors."""
    coordinator: ApplianceTrackerCoordinator = entry.runtime_data

    async_add_entities([ApplianceRunningBinarySensor(coordinator, entry)])


class ApplianceRunningBinarySensor(
    CoordinatorEntity[ApplianceTrackerCoordinator], BinarySensorEntity
):
    """Binary sensor indicating if the appliance is currently running."""

    _attr_has_entity_name = True
    _attr_translation_key = "running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: ApplianceTrackerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_running"
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
    def is_on(self) -> bool:
        """Return true if the appliance is running."""
        return self.coordinator.is_running
