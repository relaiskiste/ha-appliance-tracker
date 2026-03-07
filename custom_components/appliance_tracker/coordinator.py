"""Data coordinator for Appliance Tracker."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_APPLIANCE_NAME,
    CONF_APPLIANCE_TYPE,
    CONF_COMPLETE_TIMEOUT,
    CONF_FINISHING_DELAY,
    CONF_POWER_SENSOR,
    CONF_START_DELAY,
    CONF_START_THRESHOLD,
    CONF_STOP_DELAY,
    CONF_STOP_THRESHOLD,
    DEFAULT_COMPLETE_TIMEOUT,
    DEFAULT_FINISHING_DELAY,
    DEFAULT_START_DELAY,
    DEFAULT_STOP_DELAY,
    DOMAIN,
    ApplianceState,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = f"{DOMAIN}.history"


class ApplianceTrackerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that tracks appliance state based on power consumption."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self._entry = entry
        self._power_sensor: str = entry.data[CONF_POWER_SENSOR]
        self._appliance_name: str = entry.data[CONF_APPLIANCE_NAME]
        self._appliance_type: str = entry.data[CONF_APPLIANCE_TYPE]
        self._start_threshold: float = entry.data[CONF_START_THRESHOLD]
        self._stop_threshold: float = entry.data[CONF_STOP_THRESHOLD]
        self._start_delay: int = entry.data.get(CONF_START_DELAY, DEFAULT_START_DELAY)
        self._stop_delay: int = entry.data.get(CONF_STOP_DELAY, DEFAULT_STOP_DELAY)
        self._finishing_delay: int = entry.data.get(
            CONF_FINISHING_DELAY, DEFAULT_FINISHING_DELAY
        )
        self._complete_timeout: int = entry.data.get(
            CONF_COMPLETE_TIMEOUT, DEFAULT_COMPLETE_TIMEOUT
        )

        # State machine
        self._state: ApplianceState = ApplianceState.IDLE
        self._current_power: float = 0.0
        self._state_change_time: datetime | None = None
        self._cycle_start: datetime | None = None
        self._cycle_energy_start: float | None = None

        # History
        self._cycle_count: int = 0
        self._last_cycle_duration: float | None = None
        self._last_cycle_energy: float | None = None

        # Timers
        self._unsub_state_change: CALLBACK_TYPE | None = None
        self._unsub_timer: CALLBACK_TYPE | None = None

        # Persistent storage
        self._store = Store[dict[str, Any]](
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}.{entry.entry_id}"
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=30),
        )

    @property
    def appliance_name(self) -> str:
        """Return the appliance name."""
        return self._appliance_name

    @property
    def appliance_type(self) -> str:
        """Return the appliance type."""
        return self._appliance_type

    @property
    def appliance_state(self) -> ApplianceState:
        """Return the current appliance state."""
        return self._state

    @property
    def current_power(self) -> float:
        """Return the current power reading."""
        return self._current_power

    @property
    def is_running(self) -> bool:
        """Return True if the appliance is running."""
        return self._state in (ApplianceState.RUNNING, ApplianceState.FINISHING)

    @property
    def cycle_start(self) -> datetime | None:
        """Return the current cycle start time."""
        return self._cycle_start

    @property
    def cycle_count(self) -> int:
        """Return the total cycle count."""
        return self._cycle_count

    @property
    def last_cycle_duration(self) -> float | None:
        """Return last cycle duration in minutes."""
        return self._last_cycle_duration

    @property
    def last_cycle_energy(self) -> float | None:
        """Return last cycle energy in kWh."""
        return self._last_cycle_energy

    @property
    def start_threshold(self) -> float:
        """Return the start threshold."""
        return self._start_threshold

    @property
    def stop_threshold(self) -> float:
        """Return the stop threshold."""
        return self._stop_threshold

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        # Load persisted history
        stored = await self._store.async_load()
        if stored:
            self._cycle_count = stored.get("cycle_count", 0)
            self._last_cycle_duration = stored.get("last_cycle_duration")
            self._last_cycle_energy = stored.get("last_cycle_energy")
            _LOGGER.debug(
                "Loaded history for %s: %d cycles",
                self._appliance_name,
                self._cycle_count,
            )

        # Subscribe to power sensor state changes
        self._unsub_state_change = async_track_state_change_event(
            self.hass, [self._power_sensor], self._async_power_state_changed
        )

        # Read current state
        state = self.hass.states.get(self._power_sensor)
        if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._current_power = float(state.state)
            except (ValueError, TypeError):
                self._current_power = 0.0

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        if self._unsub_state_change:
            self._unsub_state_change()
            self._unsub_state_change = None
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        await self._async_save_history()

    @callback
    def _async_power_state_changed(self, event) -> None:
        """Handle power sensor state changes."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ):
            return

        try:
            self._current_power = float(new_state.state)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid power value from %s: %s",
                self._power_sensor,
                new_state.state,
            )
            return

        self._process_state_machine()
        self.async_set_updated_data(self._build_data())

    def _process_state_machine(self) -> None:
        """Process the appliance state machine based on current power."""
        now = dt_util.utcnow()
        power = self._current_power

        if self._state == ApplianceState.IDLE:
            if power >= self._start_threshold:
                if self._state_change_time is None:
                    self._state_change_time = now
                elif (now - self._state_change_time).total_seconds() >= self._start_delay:
                    self._transition_to(ApplianceState.RUNNING, now)
            else:
                self._state_change_time = None

        elif self._state == ApplianceState.RUNNING:
            if power < self._stop_threshold:
                if self._state_change_time is None:
                    self._state_change_time = now
                elif (now - self._state_change_time).total_seconds() >= self._stop_delay:
                    self._transition_to(ApplianceState.FINISHING, now)
            else:
                # Reset stop timer if power goes back up
                self._state_change_time = None

        elif self._state == ApplianceState.FINISHING:
            if power >= self._start_threshold:
                # Appliance resumed — back to running
                self._transition_to(ApplianceState.RUNNING, now)
            elif power < self._stop_threshold:
                if self._state_change_time is None:
                    self._state_change_time = now
                elif (
                    now - self._state_change_time
                ).total_seconds() >= self._finishing_delay:
                    self._transition_to(ApplianceState.COMPLETE, now)
            else:
                self._state_change_time = None

        elif self._state == ApplianceState.COMPLETE:
            if self._state_change_time and (
                now - self._state_change_time
            ).total_seconds() >= self._complete_timeout:
                self._transition_to(ApplianceState.IDLE, now)

    def _transition_to(self, new_state: ApplianceState, now: datetime) -> None:
        """Handle state transition."""
        old_state = self._state
        self._state = new_state
        self._state_change_time = now

        _LOGGER.info(
            "%s: %s → %s (power: %.1fW)",
            self._appliance_name,
            old_state,
            new_state,
            self._current_power,
        )

        if new_state == ApplianceState.RUNNING and old_state == ApplianceState.IDLE:
            self._cycle_start = now
            self._cycle_energy_start = self._current_power

        elif new_state == ApplianceState.COMPLETE:
            self._complete_cycle(now)

        elif new_state == ApplianceState.IDLE:
            self._cycle_start = None
            self._state_change_time = None

    def _complete_cycle(self, now: datetime) -> None:
        """Record a completed cycle."""
        self._cycle_count += 1

        if self._cycle_start:
            duration_seconds = (now - self._cycle_start).total_seconds()
            self._last_cycle_duration = round(duration_seconds / 60, 1)
        else:
            self._last_cycle_duration = None

        # Energy estimation (simplified — power-based approximation)
        # For accurate energy tracking, users should pair with an energy sensor
        self._last_cycle_energy = None

        _LOGGER.info(
            "%s: Cycle #%d complete. Duration: %s min",
            self._appliance_name,
            self._cycle_count,
            self._last_cycle_duration,
        )

        # Fire an event for automations
        self.hass.bus.async_fire(
            f"{DOMAIN}_cycle_complete",
            {
                "appliance_name": self._appliance_name,
                "appliance_type": self._appliance_type,
                "cycle_count": self._cycle_count,
                "duration_minutes": self._last_cycle_duration,
                "entry_id": self._entry.entry_id,
            },
        )

        # Persist history
        self.hass.async_create_task(self._async_save_history())

    async def _async_save_history(self) -> None:
        """Save cycle history to storage."""
        await self._store.async_save(
            {
                "cycle_count": self._cycle_count,
                "last_cycle_duration": self._last_cycle_duration,
                "last_cycle_energy": self._last_cycle_energy,
            }
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Periodic update — re-evaluate state machine."""
        self._process_state_machine()
        return self._build_data()

    def _build_data(self) -> dict[str, Any]:
        """Build the data dict for entities."""
        return {
            "state": self._state,
            "power": self._current_power,
            "is_running": self.is_running,
            "cycle_start": self._cycle_start.isoformat() if self._cycle_start else None,
            "cycle_count": self._cycle_count,
            "last_cycle_duration": self._last_cycle_duration,
            "last_cycle_energy": self._last_cycle_energy,
        }
