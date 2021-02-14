"""The SenseME integration."""
import asyncio
import logging

from aiosenseme import SensemeDevice
from aiosenseme import __version__ as aiosenseme_version
from aiosenseme import async_get_device_by_device_info
from homeassistant.components.binary_sensor import DOMAIN as BINARYSENSOR_DOMAIN
from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_INFO,
    DISCOVERY_UPDATE_RATE,
    DOMAIN,
    EVENT_SENSEME_CONFIG_UPDATE,
    UPDATE_RATE,
)

PLATFORMS = [FAN_DOMAIN, LIGHT_DOMAIN, BINARYSENSOR_DOMAIN]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the SenseME component."""
    if config.get(DOMAIN) is not None:
        _LOGGER.error(
            "Configuration of senseme integration via yaml is depreciated, "
            "instead use Home Assistant frontend to add this integration"
        )

    hass.data.setdefault(DOMAIN, {})

    # # Make sure SenseME Discovery is already running
    # if hass.data.get(DOMAIN) is None:
    #     # Discovery not already started
    #     discovery = SensemeDiscovery(False, DISCOVERY_UPDATE_RATE)
    #     discovery.start()
    #     hass.data[DOMAIN]["discovery"] = discovery

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SenseME from a config entry."""

    async def _async_config_entry_updated(hass, entry) -> None:
        """Handle signals of config entry being updated."""
        print(f"Device Options Updated {entry.options}")
        async_dispatcher_send(hass, EVENT_SENSEME_CONFIG_UPDATE)

    async def _setup_platforms():
        """Set up platforms and initiate connection."""
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_setup(entry, component)
                for component in PLATFORMS
            ]
        )

    # print(f"Config Entry={entry.as_dict()}")
    hass.data[DOMAIN][entry.unique_id] = {}
    device = await async_get_device_by_device_info(
        info=entry.data[CONF_INFO], ignore_errors=True, refresh_minutes=UPDATE_RATE
    )
    await device.async_update()
    hass.data[DOMAIN][entry.unique_id][CONF_DEVICE] = device
    entry.add_update_listener(_async_config_entry_updated)
    hass.async_create_task(_setup_platforms())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN][entry.unique_id][CONF_DEVICE].stop()
        hass.data[DOMAIN][entry.unique_id] = None
    return True
