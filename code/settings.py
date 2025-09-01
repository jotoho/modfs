#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from enum import Enum
from pathlib import Path
from re import match, IGNORECASE, NOFLAG
from sys import stderr
from typing import *

from code.mod import meets_requirements
from code.paths import get_meta_directory

TSetting = TypeVar("TSetting")

transform_overrides = list[tuple[Callable[[str], bool], Callable[[str], TSetting]]]
filter_predicate = Callable[[TSetting], bool]


def bool_cast_fn() -> transform_overrides:
    return [
        (lambda s: match("^true$", s, IGNORECASE) is not None, lambda unused: True),
        (lambda s: match("^false$", s, IGNORECASE) is not None, lambda unused: False),
        (lambda s: match("^[0-9]+$", s, NOFLAG) is not None, lambda s: int(s) != 0)
    ]


default_cast_funcs: dict[type, Callable[[], transform_overrides]] = {
    bool: bool_cast_fn
}


class ValidInstanceSettings(Enum):
    def __init__(self,
                 setting_id: str,
                 value_type: Type[TSetting],
                 default: TSetting,
                 requirements: Iterable[filter_predicate],
                 use_complex_cast: bool = False,
                 custom_casts: transform_overrides | None = None) -> None:
        super().__init__()
        if None in [setting_id, value_type, requirements]:
            raise ValueError("None was illegally passed to ValidInstanceSettings constructor")
        elif match(r'[^a-z]', setting_id, IGNORECASE):
            raise ValueError(f"setting id {setting_id} does not meet name requirements")
        self.setting_id = setting_id
        self.value_type = value_type
        self.default = default

        self.requirements: frozenset[filter_predicate] = frozenset(requirements).union({
            lambda value: value is None or isinstance(value, value_type)
        })

        assert meets_requirements(self.default, self.requirements)

        if use_complex_cast and custom_casts is not None:
            self.cast_funcs: transform_overrides = custom_casts
        elif use_complex_cast and value_type in default_cast_funcs.keys():
            self.cast_funcs: transform_overrides = default_cast_funcs[value_type]()
        else:
            self.cast_funcs: transform_overrides = []
        # Fallback to type constructor
        self.cast_funcs.append((lambda unused: True, value_type))

    DEPLOYMENT_TARGET_DIR = ("deploymentTargetDir",
                             Path,
                             None,
                             [lambda val: val is None or val.is_dir()])
    FILESYSTEM_WORK_DIR = ("deploymentWorkDir",
                           Path,
                           None,
                           [])
    FILESYSTEM_OVERFLOW_DIR = ("deploymentOverflowDir",
                               Path,
                               None,
                               [])
    DEFAULT_MOD_SUBFOLDER = ("defaultModSubfolder",
                             str,
                             "./",
                             [])
    SUPPRESS_DEVELOPER_CMD_WARNING = ("suppressDeveloperWarning",
                                      bool,
                                      False,
                                      [],
                                      True)
    FILES_CASING_POLICY = ("normalizeCase",
                           str,
                           "all",
                           [lambda s: s in ["all", "folders", "none"]])


class InstanceSettings:
    def __init__(self, instance_path: Path) -> None:
        self.settingsPath = get_meta_directory(instance_path) / "settings"

    def initialize_settings_directory(self) -> None:
        self.settingsPath.mkdir(parents=True, exist_ok=True)

    def get_file_path(self, setting: ValidInstanceSettings) -> Path:
        return self.settingsPath / setting.setting_id.lower()

    def get(self, setting: ValidInstanceSettings, force_retrieval: bool = False) -> TSetting | None:
        try:
            file_contents: str = (self.get_file_path(setting)
                                  .read_text(encoding="UTF-8")
                                  .strip())
            applicable_casts = list(map(lambda c: c[1],
                                        filter(lambda c: c[0](file_contents),
                                               setting.cast_funcs)))
            assert len(applicable_casts) >= 1
            cast_value: TSetting = applicable_casts[0](file_contents)
            if meets_requirements(cast_value, setting.requirements) or force_retrieval:
                return cast_value
            else:
                print(f"Setting value {cast_value} in {setting.setting_id} is invalid or does "
                      "not meet all requirements!", file=stderr)
                from os import EX_DATAERR
                exit(EX_DATAERR)
        except (FileNotFoundError, IsADirectoryError):
            # The default value is ALWAYS allowed to be None
            return setting.default
        except PermissionError:
            print(f"Could not read setting {setting.setting_id}. Ensure that the entire instance "
                  "directory is readable!", file=stderr)
            from os import EX_IOERR
            exit(EX_IOERR)

    def set(self, setting: ValidInstanceSettings, value: TSetting) -> None:
        if not meets_requirements(value, setting.requirements):
            raise ValueError(f"Tried to write invalid value '{value}' to setting"
                             f" {setting.setting_id}")
        # Always try to use instance-relative paths, if possible.
        if isinstance(value, Path):
            from code.mod import attempt_instance_relative_cast
            value = attempt_instance_relative_cast(value)
        try:
            self.get_file_path(setting).write_text(data=str(value) + '\n', encoding='UTF-8')
        except IsADirectoryError:
            print(f"Failed to write new value to {setting.setting_id}. The target location is a "
                  "directory! This damage will need to be corrected manually.", file=stderr)
            from os import EX_IOERR
            exit(EX_IOERR)
        except PermissionError:
            print(f"Failed to write new value to {setting.setting_id}. "
                  "Ensure that the instance directory can be written to!", file=stderr)
            from os import EX_IOERR
            exit(EX_IOERR)

    def unset(self, setting: ValidInstanceSettings) -> None:
        setting_file: Path = self.get_file_path(setting)
        try:
            if setting_file.is_file():
                setting_file.unlink(missing_ok=True)
        except PermissionError:
            print(f"Failed to write new value to {setting.setting_id}. "
                  "Ensure that the instance directory can be written to!", file=stderr)
            from os import EX_IOERR
            exit(EX_IOERR)

    def is_set(self, setting: ValidInstanceSettings) -> bool:
        return self.get_file_path(setting).is_file()


instance_settings: InstanceSettings | None = None


def set_instance_settings(setting: InstanceSettings) -> None:
    global instance_settings
    if setting is not None:
        instance_settings = setting


def get_instance_settings() -> InstanceSettings:
    return instance_settings
