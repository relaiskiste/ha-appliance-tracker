"""The Appliance Tracker integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import ApplianceTrackerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type ApplianceTrackerConfigEntry = ConfigEntry[ApplianceTrackerCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: ApplianceTrackerConfigEntry
) -> bool:
    """Set up Appliance Tracker from a config entry."""
    coordinator = ApplianceTrackerCoordinator(hass, entry)
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(coordinator.async_shutdown)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ApplianceTrackerConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
