#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from collections import OrderedDict
from pathlib import Path
from subprocess import call
from pprint import pp

from psutil import disk_partitions

from code.mod import get_mod_mount_path
from code.settings import InstanceSettings, ValidInstanceSettings, get_instance_settings
from code.commandline import get_instance_path


def are_paths_on_same_filesystem(path1: Path, path2: Path) -> bool:
    from os import stat
    # Get the device or filesystem identifier for each path
    dev1 = stat(path1).st_dev
    dev2 = stat(path2).st_dev

    # Compare the identifiers to check if they are the same
    return dev1 == dev2


def is_fuse_overlayfs_mounted(target_directory: Path | None = None) -> bool:
    if target_directory is None:
        target_directory = get_instance_settings().get(ValidInstanceSettings.DEPLOYMENT_TARGET_DIR)
    partitions = disk_partitions(all=True)
    for partition in partitions:
        if partition.fstype == 'fuse.fuse-overlayfs':
            if partition.mountpoint == str(target_directory.resolve()):
                return True
    return False


def get_or_create_overflow_dir() -> Path:
    from code.mod import resolve_base_dir
    configured_overflow_dir: Path | None = InstanceSettings(resolve_base_dir()).get(
        ValidInstanceSettings.FILESYSTEM_OVERFLOW_DIR)
    overflow_dir = (configured_overflow_dir if configured_overflow_dir is not None
                    else Path('modifiedfiles'))
    if not overflow_dir.is_absolute():
        overflow_dir = resolve_base_dir() / overflow_dir
    overflow_dir.mkdir(parents=True, exist_ok=True)
    return overflow_dir


def get_or_create_work_dir() -> Path:
    from code.mod import resolve_base_dir
    configured_work_dir: Path | None = InstanceSettings(resolve_base_dir()).get(
        ValidInstanceSettings.FILESYSTEM_WORK_DIR)
    work_dir = (configured_work_dir if configured_work_dir is not None
                else Path('working_cache'))
    if not work_dir.is_absolute():
        work_dir = resolve_base_dir() / work_dir
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


def deploy_filesystem(target_dir: Path,
                      mods_to_deploy: OrderedDict[str, tuple[str, str]]) -> None:
    assert target_dir is not None
    assert target_dir.is_dir()
    if not is_fuse_overlayfs_mounted(target_dir):
        mod_dirs = str(target_dir)
        for mod in mods_to_deploy.keys():
            date, subversion = mods_to_deploy[mod]
            mod_dir = get_mod_mount_path(mod, date, subversion)
            if mod_dir.is_dir():
                mod_dirs = f"{str(mod_dir)}:{mod_dirs}"
        overflow_dir = get_or_create_overflow_dir()
        work_dir = get_or_create_work_dir()
        if not are_paths_on_same_filesystem(target_dir, work_dir):
            from sys import stderr
            print("work directory must be on the same filesystem as target",
                  file=stderr)
            exit(1)
        print("Lower directories:")
        print(mod_dirs.replace(":", "\n").replace(str(get_instance_path()), "."))
        print()
        command = ["fuse-overlayfs",
                   "-o", "volatile",
                   "-o", "noacl",
                   "-o", "nodev",
                   "-o", "nosuid",
                   "-o", "noatime",
                   "-o", f"lowerdir={mod_dirs}",
                   "-o", f"workdir={work_dir}",
                   "-o", f"upperdir={overflow_dir}",
                   str(target_dir)]
        print("Command:")
        pp([s if not s.startswith("lowerdir=") else "lowerdir=\u2026" for s in command], compact=True)
        call(command)
    else:
        from sys import stderr
        print("Something is already mounted at the destination!", file=stderr)
        exit(1)


def stop_filesystem(target_dir: Path) -> None:
    if is_fuse_overlayfs_mounted(target_dir):
        call(["fusermount3", "-u", str(target_dir.resolve())])
    else:
        from sys import stderr
        print("Attempted to stop a filesystem that is not running", file=stderr)
        exit(1)
