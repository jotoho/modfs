#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only

from enum import Enum
from pathlib import Path
from typing import Callable, TypeVar, Type, Any, Iterable
from code.mod import validate_mod_id, mod_exists, resolve_base_dir
from re import match, IGNORECASE, NOFLAG, search

TSetting = TypeVar("TSetting")

filter_predicate = Callable[[TSetting], bool]


class ValidModSettings(Enum):
    def __init__(self,
                 key: str,
                 value_type: Type[TSetting],
                 default: TSetting,
                 requirements: Iterable[filter_predicate]) -> None:
        self.key: str = key
        self.value_type: Type[TSetting] = value_type
        self.default: TSetting = default
        self.requirements: frozenset[filter_predicate] = frozenset(requirements).union({
            lambda value: isinstance(value, value_type)
        })

    ENABLED = ("enabled", bool, True, {})
    PRETTY_NAME = ("pretty_name", str, "", {
        lambda s: match(r"^[a-z0-9\- ]*$", s, IGNORECASE) is not None,
        lambda s: match(r"^[\s]+", s, NOFLAG) is None,
        lambda s: search(r"[\s]+$", s, NOFLAG) is None,
    })
    AUTHOR = ("author", str, "", {
        lambda s: match(r"^[a-z0-9 ]*$", s, IGNORECASE) is not None,
        lambda s: match(r"^[\s]+", s, NOFLAG) is None,
        lambda s: search(r"[\s]+$", s, NOFLAG) is None,
    })
    MOD_VERSION = ("use_mod_version", str, "latest", {
        lambda s: match(r"^((latest)|([0-9]{4,}-[0-9]{2}-[0-9]{2}/[0-9]{2}))$", s) is not None,
    })
    NOTES = ("custom_notes", str, "", {})


def default_mod_settings() -> dict[str, Any]:
    return dict(map(lambda setting: (setting.key, setting.default), ValidModSettings))


ReqVal = TypeVar("ReqVal")


def meets_requirements(value: ReqVal, conditions: Iterable[Callable[[ReqVal], bool]]) -> bool:
    return all((fn(value) for fn in conditions))


class ModConfig:
    def __init__(self, mod_id: str, base_dir: Path | None = None):
        self.base_dir: Path = resolve_base_dir(base_dir)
        if not validate_mod_id(mod_id) or not mod_exists(mod_id, base_dir=self.base_dir):
            raise ValueError("tried to access mod configuration for non-existent mod")
        self.mod_id = mod_id

    def conf_file(self):
        return self.base_dir / 'mods' / f"{self.mod_id}.json"

    def get_all(self, insert_defaults: bool = True) -> dict[str, Any]:
        try:
            with self.conf_file().open("rt") as f:
                from json import load
                values: dict[str, Any] = load(f)
                if insert_defaults:
                    return default_mod_settings() | values
                else:
                    return values
        except FileNotFoundError:
            return default_mod_settings() if insert_defaults else {}

    def get(self, setting: ValidModSettings) -> Any:
        try:
            with self.conf_file().open("rt") as f:
                from json import load
                values: dict[str, Any] = load(f)
                value = values[setting.key] if setting.key in values.keys() else setting.default
                if meets_requirements(value, setting.requirements):
                    return value
                else:
                    raise ValueError(f"Value {setting.default} for setting {setting.key} of mod "
                                     f"{self.mod_id} is invalid")
        except FileNotFoundError:
            if meets_requirements(setting.default, setting.requirements):
                return setting.default
            else:
                raise ValueError(f"Value {setting.default} for setting {setting.key} of mod "
                                 f"{self.mod_id} is invalid")

    def set(self, setting: ValidModSettings, value: Any) -> None:
        if not meets_requirements(value, setting.requirements):
            raise ValueError(f"Tried to save invalid value {value} to setting {setting.key} for "
                             f"mod {self.mod_id}")
        # Get old values BEFORE overwriting them :)
        prev_settings = self.get_all(insert_defaults=False)
        with self.conf_file().open("wt") as f:
            from json import dump
            dump(prev_settings | {setting.key: value}, f, indent=2, sort_keys=True)
            from os import linesep
            f.write(linesep)


def mod_change_activation(mod_id: str, enable_status: bool, base_dir: Path | None = None) -> None:
    mod_settings = ModConfig(mod_id, resolve_base_dir(base_dir))
    mod_settings.set(ValidModSettings.ENABLED, enable_status)
