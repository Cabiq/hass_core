"""Support for esphome domain data."""
from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass, field
from typing import cast

from bleak.backends.service import BleakGATTServiceCollection
from lru import LRU  # pylint: disable=no-name-in-module
from typing_extensions import Self

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder

from .const import DOMAIN
from .entry_data import ESPHomeStorage, RuntimeEntryData

STORAGE_VERSION = 1
MAX_CACHED_SERVICES = 128


@dataclass
class DomainData:
    """Define a class that stores global esphome data in hass.data[DOMAIN]."""

    _entry_datas: dict[str, RuntimeEntryData] = field(default_factory=dict)
    _stores: dict[str, ESPHomeStorage] = field(default_factory=dict)
    _gatt_services_cache: MutableMapping[int, BleakGATTServiceCollection] = field(
        default_factory=lambda: LRU(MAX_CACHED_SERVICES)
    )
    _gatt_mtu_cache: MutableMapping[int, int] = field(
        default_factory=lambda: LRU(MAX_CACHED_SERVICES)
    )

    def get_gatt_services_cache(
        self, address: int
    ) -> BleakGATTServiceCollection | None:
        """Get the BleakGATTServiceCollection for the given address."""
        return self._gatt_services_cache.get(address)

    def set_gatt_services_cache(
        self, address: int, services: BleakGATTServiceCollection
    ) -> None:
        """Set the BleakGATTServiceCollection for the given address."""
        self._gatt_services_cache[address] = services

    def clear_gatt_services_cache(self, address: int) -> None:
        """Clear the BleakGATTServiceCollection for the given address."""
        self._gatt_services_cache.pop(address, None)

    def get_gatt_mtu_cache(self, address: int) -> int | None:
        """Get the mtu cache for the given address."""
        return self._gatt_mtu_cache.get(address)

    def set_gatt_mtu_cache(self, address: int, mtu: int) -> None:
        """Set the mtu cache for the given address."""
        self._gatt_mtu_cache[address] = mtu

    def clear_gatt_mtu_cache(self, address: int) -> None:
        """Clear the mtu cache for the given address."""
        self._gatt_mtu_cache.pop(address, None)

    def get_entry_data(self, entry: ConfigEntry) -> RuntimeEntryData:
        """Return the runtime entry data associated with this config entry.

        Raises KeyError if the entry isn't loaded yet.
        """
        return self._entry_datas[entry.entry_id]

    def set_entry_data(self, entry: ConfigEntry, entry_data: RuntimeEntryData) -> None:
        """Set the runtime entry data associated with this config entry."""
        if entry.entry_id in self._entry_datas:
            raise ValueError("Entry data for this entry is already set")
        self._entry_datas[entry.entry_id] = entry_data

    def pop_entry_data(self, entry: ConfigEntry) -> RuntimeEntryData:
        """Pop the runtime entry data instance associated with this config entry."""
        return self._entry_datas.pop(entry.entry_id)

    def get_or_create_store(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> ESPHomeStorage:
        """Get or create a Store instance for the given config entry."""
        return self._stores.setdefault(
            entry.entry_id,
            ESPHomeStorage(
                hass, STORAGE_VERSION, f"esphome.{entry.entry_id}", encoder=JSONEncoder
            ),
        )

    @classmethod
    def get(cls, hass: HomeAssistant) -> Self:
        """Get the global DomainData instance stored in hass.data."""
        # Don't use setdefault - this is a hot code path
        if DOMAIN in hass.data:
            return cast(Self, hass.data[DOMAIN])
        ret = hass.data[DOMAIN] = cls()
        return ret
