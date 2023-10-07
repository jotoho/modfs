#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from enum import Enum
from pathlib import Path
from re import match, IGNORECASE
from sys import stderr
from typing import *

TSetting = TypeVar("TSetting")


class ValidInstanceSettings(Enum):
    def __init__(self,
                 setting_id: str,
                 value_type: Type[TSetting],
                 default: TSetting,
                 validator: Callable[[TSetting], bool]) -> None:
        super().__init__()
        if match(r'[^a-z]', setting_id, IGNORECASE):
            raise ValueError("")
        self.setting_id = setting_id.lower()
        self.value_type = value_type
        self.default = default
        self.validator = validator

    BACKGROUND_DEPLOYMENT = ("deployInBackground",
                             bool,
                             False,
                             lambda val: isinstance(val, bool))
    DEPLOYMENT_TARGET_DIR = ("deploymentTargetDir",
                             Path,
                             None,
                             lambda val: isinstance(val, Path) and val.is_dir())
    FILESYSTEM_WORK_DIR = ("deploymentWorkDir",
                           Path,
                           None,
                           lambda val: isinstance(val, Path))
    FILESYSTEM_OVERFLOW_DIR = ("deploymentOverflowDir",
                               Path,
                               None,
                               lambda val: isinstance(val, Path))
    DEFAULT_MOD_SUBFOLDER = ("defaultModSubfolder",
                             str,
                             "./",
                             lambda val: isinstance(val, str))


class InstanceSettings:
    def __init__(self, instance_path: Path) -> None:
        self.settingsPath = instance_path / ".moddingoverlay" / "settings"

    def initialize_settings_directory(self) -> None:
        self.settingsPath.mkdir(parents=True, exist_ok=True)

    def get(self, setting: ValidInstanceSettings) -> TSetting | None:
        setting_file: Path = self.settingsPath / setting.setting_id
        try:
            file_contents: str = (setting_file.read_text(encoding="UTF-8")
                                  .strip())
            cast_value = setting.value_type(file_contents)
            if setting.validator(cast_value):
                return cast_value
            else:
                print(f"Setting value {cast_value} in {setting.setting_id} is invalid or does "
                      "not meet all requirements!", file=stderr)
                from os import EX_DATAERR
                exit(EX_DATAERR)
        except (FileNotFoundError, IsADirectoryError):
            return setting.default
        except PermissionError:
            print(f"Could not read setting {setting.setting_id}. Ensure that the entire instance "
                  "directory is readable!", file=stderr)
            from os import EX_IOERR
            exit(EX_IOERR)

    def set(self, setting: ValidInstanceSettings, value: TSetting) -> None:
        setting_file: Path = self.settingsPath / setting.setting_id
        try:
            setting_file.write_text(data=str(value) + '\n',
                                    encoding='UTF-8')
        except IsADirectoryError:
            print(f"Failed to write new value to {setting.setting_id}. The target location is a "
                  "directory! This damage will need to be corrected manually.", file=stderr)
        except PermissionError:
            print(f"Failed to write new value to {setting.setting_id}. "
                  "Ensure that the instance directory can be written to!", file=stderr)
            from os import EX_IOERR
            exit(EX_IOERR)


instance_settings: InstanceSettings | None = None


def set_instance_settings(setting: InstanceSettings) -> None:
    global instance_settings
    if setting is not None:
        instance_settings = setting


def get_instance_settings() -> InstanceSettings:
    return instance_settings
