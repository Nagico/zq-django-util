from typing import Dict, Optional, Union

from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver
from rest_framework.settings import import_from_string, perform_import


class PackageSettings:
    """
    Copy of DRF APISettings class with support for importing settings that
    are dicts with value as a string representing the path to the class
    to be imported.
    """

    setting_name: Optional[str] = None
    DEFAULTS: Optional[Dict[str, Union[str, int, bool, list[str]]]] = None
    IMPORT_STRINGS: Optional[list[str]] = None

    def __init__(self, defaults=None, import_strings=None):
        if self.setting_name is None:
            raise NotImplementedError("setting_name must be set")
        if self.DEFAULTS is None:
            raise NotImplementedError("DEFAULTS must be set")
        if self.IMPORT_STRINGS is None:
            raise NotImplementedError("IMPORT_STRINGS must be set")

        self.defaults = defaults or self.DEFAULTS
        self.import_strings = import_strings or self.IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self) -> Dict[str, Union[str, int, bool, list[str]]]:
        if not hasattr(self, "_user_settings"):
            assert self.setting_name is not None
            self._user_settings = getattr(settings, self.setting_name, {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            if isinstance(val, dict):
                val = {
                    status_code: import_from_string(error_schema, attr)
                    for status_code, error_schema in val.items()
                }
            else:
                val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self) -> None:
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")

    @receiver(setting_changed)
    def reload_package_settings(self, *args, **kwargs) -> None:
        setting = kwargs["setting"]
        if setting == self.setting_name:
            self.reload()
