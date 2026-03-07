"""Config flow for Appliance Tracker."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import UnitOfPower
from homeassistant.helpers import selector

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
    DEFAULT_THRESHOLDS,
    DOMAIN,
    ApplianceType,
)


class ApplianceTrackerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Appliance Tracker."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._appliance_type: str | None = None
        self._appliance_name: str | None = None
        self._power_sensor: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step — select appliance type and name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._appliance_type = user_input[CONF_APPLIANCE_TYPE]
            self._appliance_name = user_input[CONF_APPLIANCE_NAME]
            self._power_sensor = user_input[CONF_POWER_SENSOR]

            # Validate sensor exists
            state = self.hass.states.get(self._power_sensor)
            if state is None:
                errors[CONF_POWER_SENSOR] = "sensor_not_found"
            else:
                return await self.async_step_thresholds()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_APPLIANCE_NAME): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(
                        CONF_APPLIANCE_TYPE, default=ApplianceType.WASHING_MACHINE
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=ApplianceType.WASHING_MACHINE,
                                    label="Washing Machine",
                                ),
                                selector.SelectOptionDict(
                                    value=ApplianceType.DRYER,
                                    label="Dryer",
                                ),
                                selector.SelectOptionDict(
                                    value=ApplianceType.DISHWASHER,
                                    label="Dishwasher",
                                ),
                                selector.SelectOptionDict(
                                    value=ApplianceType.CUSTOM,
                                    label="Custom Appliance",
                                ),
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_POWER_SENSOR): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor",
                            device_class="power",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_thresholds(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle threshold configuration."""
        if user_input is not None:
            # Build final config
            data = {
                CONF_APPLIANCE_NAME: self._appliance_name,
                CONF_APPLIANCE_TYPE: self._appliance_type,
                CONF_POWER_SENSOR: self._power_sensor,
                CONF_START_THRESHOLD: user_input[CONF_START_THRESHOLD],
                CONF_STOP_THRESHOLD: user_input[CONF_STOP_THRESHOLD],
                CONF_START_DELAY: user_input[CONF_START_DELAY],
                CONF_STOP_DELAY: user_input[CONF_STOP_DELAY],
                CONF_FINISHING_DELAY: user_input[CONF_FINISHING_DELAY],
                CONF_COMPLETE_TIMEOUT: user_input[CONF_COMPLETE_TIMEOUT],
            }

            # Check for duplicate entries with same sensor
            await self.async_set_unique_id(
                f"{DOMAIN}_{self._power_sensor}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._appliance_name,
                data=data,
            )

        # Get defaults for selected type
        start_default, stop_default = DEFAULT_THRESHOLDS.get(
            self._appliance_type, (10.0, 5.0)
        )

        return self.async_show_form(
            step_id="thresholds",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_START_THRESHOLD, default=start_default
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=5000,
                            step=0.5,
                            unit_of_measurement=UnitOfPower.WATT,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_STOP_THRESHOLD, default=stop_default
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0.5,
                            max=5000,
                            step=0.5,
                            unit_of_measurement=UnitOfPower.WATT,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_START_DELAY, default=DEFAULT_START_DELAY
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5,
                            max=300,
                            step=5,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Required(
                        CONF_STOP_DELAY, default=DEFAULT_STOP_DELAY
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=10,
                            max=600,
                            step=10,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Required(
                        CONF_FINISHING_DELAY, default=DEFAULT_FINISHING_DELAY
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=30,
                            max=900,
                            step=30,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Required(
                        CONF_COMPLETE_TIMEOUT, default=DEFAULT_COMPLETE_TIMEOUT
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=60,
                            max=3600,
                            step=60,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
            description_placeholders={
                "appliance_name": self._appliance_name,
            },
        )
