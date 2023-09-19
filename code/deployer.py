#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from pathlib import Path
from subprocess import call

from psutil import disk_partitions

from code.mod import get_mod_mount_path
from code.settings import InstanceSettings, ValidInstanceSettings


def are_paths_on_same_filesystem(path1: Path, path2: Path) -> bool:
    from os import stat
    # Get the device or filesystem identifier for each path
    dev1 = stat(path1).st_dev
    dev2 = stat(path2).st_dev

    # Compare the identifiers to check if they are the same
    return dev1 == dev2


def is_fuse_overlayfs_mounted(target_directory: Path) -> bool:
    partitions = disk_partitions(all=True)
    for partition in partitions:
        if partition.fstype == 'fuse.fuse-overlayfs':
            if partition.mountpoint == str(target_directory.resolve()):
                return True
    return False


def get_or_create_overflow_dir() -> Path:
    from code.mod import base_directory
    configured_overflow_dir = InstanceSettings(base_directory).get(
        ValidInstanceSettings.FILESYSTEM_OVERFLOW_DIR)
    overflow_dir = (configured_overflow_dir if configured_overflow_dir is not None
                    else (base_directory / 'modifiedfiles'))
    overflow_dir.mkdir(parents=True, exist_ok=True)
    return overflow_dir


def get_or_create_work_dir() -> Path:
    from code.mod import base_directory
    configured_work_dir = InstanceSettings(base_directory).get(
        ValidInstanceSettings.FILESYSTEM_WORK_DIR)
    work_dir = (configured_work_dir if configured_work_dir is not None
                else (base_directory / 'working_cache'))
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


def deploy_filesystem(target_dir: Path,
                      mods_to_deploy: dict[str, tuple[str, str]]) -> None:
    assert target_dir is not None
    assert target_dir.is_dir()
    mod_ids = list(reversed(sorted(mods_to_deploy.keys())))
    if not is_fuse_overlayfs_mounted(target_dir):
        mod_dirs = str(target_dir)
        for mod in mod_ids:
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
        command = ["fuse-overlayfs",
                   "-o", f"lowerdir={mod_dirs}",
                   "-o", f"workdir={work_dir}",
                   "-o", f"upperdir={overflow_dir}",
                   str(target_dir)]
        print(command)
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
