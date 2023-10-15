#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from pathlib import Path


def get_meta_directory(instance_dir: Path) -> Path:
    """

    :param instance_dir: Must be a valid instance of Path pointing to an existing directory
    :type instance_dir: Path
    :return: The directory containing modfs-specific instance-level persistent data
    :rtype:
    """
    assert instance_dir is not None
    assert isinstance(instance_dir, Path)
    assert instance_dir.is_dir()
    new_path_spec = instance_dir / '.modfs'
    old_path_spec = instance_dir / '.moddingoverlay'
    if old_path_spec.is_dir() and not new_path_spec.is_dir():
        return old_path_spec
    else:
        return new_path_spec
