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

from psutil import disk_partitions

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
    mods_per_chunk = max(min(10, num_mods), ceil(sqrt(num_mods)))
    #mods_per_chunk = min(3, num_mods)
    search_distance = 1
    while num_mods % mods_per_chunk == 1:
        if num_mods % (mods_per_chunk - search_distance) != 1:
            mods_per_chunk -= search_distance
        elif num_mods % (mods_per_chunk + search_distance) != 1:
            mods_per_chunk += search_distance
        else:
            search_distance += 1
    mod_dirs = []
    for mod in mods_to_deploy.keys():
        date, subversion = mods_to_deploy[mod]
        mod_dir = get_mod_mount_path(mod, date, subversion)
        if mod_dir.is_dir():
            mod_dirs = [str(mod_dir)] + mod_dirs
    link_dir_base = get_instance_settings().get(ValidInstanceSettings.MOUNT_SYMLINKS_DIR)
    links = []
    link_dir_base.mkdir(exist_ok=True, parents=True)
    clean_old_links(link_dir_base)
    for mod_linkidx in range(num_mods):
        link_dir = link_dir_base / str(mod_linkidx)
        link_dir.symlink_to(mod_dirs[mod_linkidx], target_is_directory=True)
        links += [str(link_dir)]
    overflow_dir = get_or_create_overflow_dir()
    work_dir = get_or_create_work_dir()
    if not are_paths_on_same_filesystem(target_dir, work_dir):
        print("work directory must be on the same filesystem as target", file=stderr)
        exit(1)
    print("Source directories:")
    print(str(mod_dirs).replace(str(get_instance_path()), ".") + "\n", flush=True)
    pid_path = get_pid_path()
    pid_path.touch(exist_ok=True)
    chunks_basedir = get_instance_settings().get(ValidInstanceSettings.MOUNT_CHUNKS_DIR)
    chunks_basedir.mkdir(exist_ok=True, parents=True)
    chunks_dirs = []
    for chunk_num in range(ceil(num_mods / mods_per_chunk)):
        chunk_dir = chunks_basedir / str(chunk_num)
        chunk_dir.mkdir(exist_ok=True)
        chunks_dirs += [chunk_dir]
    overlay_cmd_base = "mount --exclusive --onlyonce -t overlay overlay"
    overlay_opts = "noauto,async,nodev,nosuid,noatime,exec,userxattr"
    mount_cmd_rw = f"{overlay_cmd_base} -o '{overlay_opts},workdir={work_dir},upperdir={overflow_dir},lowerdir="
    mount_cmd_ro = f"{overlay_cmd_base} --read-only -o '{overlay_opts},ro,lowerdir="
    print(f"Splitting {num_mods} mods into {ceil(num_mods / mods_per_chunk)} chunks of max size {mods_per_chunk}", file=stderr)
    namespace_proc = Popen([
        "unshare",
        "--user",
        "--mount",
        "--map-root-user", "--", "/bin/bash"
    ], stdin=PIPE, text=True)
    pid_path.write_text(str(namespace_proc.pid) + "\n")
    with namespace_proc.stdin as cmdrelay:
        print("set -euxo pipefail", file=cmdrelay)
        for chunk_dir in chunks_dirs:
            print(mount_cmd_ro + reduce(lambda s1,s2: s1+":"+s2, links[:mods_per_chunk]) + "' '" + str(chunk_dir) + "'", file=cmdrelay)
            links = links[mods_per_chunk:]
        print(mount_cmd_rw + reduce(lambda s1,s2: s1+":"+s2, map(lambda p: str(p), chunks_dirs)) + "' '" + str(target_dir) + "'", file=cmdrelay)
        command_str = "'" + reduce(lambda s1,s2: s1+"' '"+s2, command) + "'"
        print("Executing: " + command_str)
        print(command_str, file=cmdrelay)
        print("umount --lazy --read-only '" + str(target_dir) + "'", file=cmdrelay)
    exit_code = namespace_proc.wait()

    clean_old_links(link_dir_base)

    print("Exiting with code " + str(exit_code), file=stderr, flush=True)
    exit(exit_code)
