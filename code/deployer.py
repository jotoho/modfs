#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from collections import OrderedDict
from pathlib import Path
from subprocess import call, Popen, PIPE
from pprint import pp
from sys import exit, stderr
from os import kill
from signal import SIGTERM
from time import time
from functools import reduce
from tempfile import NamedTemporaryFile
from math import sqrt, ceil

from code.mod import get_mod_mount_path
from code.settings import InstanceSettings, ValidInstanceSettings, get_instance_settings
from code.commandline import get_instance_path, get_pid_path


def are_paths_on_same_filesystem(path1: Path, path2: Path) -> bool:
    from os import stat
    # Get the device or filesystem identifier for each path
    dev1 = stat(path1).st_dev
    dev2 = stat(path2).st_dev

    # Compare the identifiers to check if they are the same
    return dev1 == dev2

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


def clean_old_links(links_dir) -> None:
    for old_link in links_dir.iterdir():
        if old_link.is_symlink():
            old_link.unlink()


def run_in_filesystem(target_dir: Path,
                      mods_to_deploy: OrderedDict[str, tuple[str, str]],
                      command: str) -> None:
    assert target_dir is not None
    assert target_dir.is_dir()
    num_mods = len(mods_to_deploy)
    if num_mods < 1:
        print("Error: Must have at least one source folder for deployment", file=stderr)
        exit(1)
    mod_dirs = []
    for mod in mods_to_deploy.keys():
        date, subversion = mods_to_deploy[mod]
        mod_dir = get_mod_mount_path(mod, date, subversion)
        if mod_dir.is_dir():
            mod_dirs = [str(mod_dir)] + mod_dirs
    overflow_dir = get_or_create_overflow_dir()
    work_dir = get_or_create_work_dir()
    if not are_paths_on_same_filesystem(overflow_dir, work_dir):
        print("work directory must be on the same filesystem as overflow", file=stderr)
        exit(1)
    print("Source directories:", file=stderr)
    pp(list(map(lambda s: str(s).replace(str(get_instance_path()), "."), mod_dirs)), stream=stderr)
    pid_path = get_pid_path()
    pid_path.touch(exist_ok=True)
    mount_cmd = f"mount --exclusive --onlyonce -t overlay overlay -o nodev,nosuid,noatime,userxattr -o 'workdir={work_dir}' -o 'upperdir={overflow_dir}' -o 'lowerdir+="
    print(f"Mounting {num_mods} sources for overlay...", file=stderr)
    namespace_proc = Popen([
        "unshare",
        "--user",
        "--mount",
        "--map-root-user", "--", "/bin/bash"
    ], stdin=PIPE, text=True)
    pid_path.write_text(str(namespace_proc.pid) + "\n")
    with namespace_proc.stdin as cmdrelay:
        print("set -euo pipefail", file=cmdrelay)
        lowerdir_concat_fn = lambda s1,s2: s1+"' -o lowerdir+='"+s2
        print(mount_cmd + reduce(lowerdir_concat_fn, map(lambda p: str(p), mod_dirs)) + "' '" + str(target_dir) + "'", file=cmdrelay)
        command_str = "'" + reduce(lambda s1,s2: s1+"' '"+s2, command) + "'"
        print("Executing: " + command_str, file=stderr)
        print(command_str, file=cmdrelay)
        print("umount --lazy --read-only '" + str(target_dir) + "'", file=cmdrelay)
        print("rm -rf '" + str(work_dir) + "/'*", file=cmdrelay)
    exit_code = namespace_proc.wait()

    if exit_code != 0:
        print("Exiting with code " + str(exit_code), file=stderr)
    exit(exit_code)
