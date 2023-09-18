#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from argparse import Namespace
from pathlib import Path
from shutil import copy, move, copytree
from sys import stderr
from typing import Callable

from code.creation import create_mod_space, recursive_lower_case_rename
from code.deployer import deploy_filesystem, stop_filesystem
from code.mod import get_mod_ids, get_mod_versions, select_latest_version
from code.settings import InstanceSettings, ValidInstanceSettings, instance_settings


def subcommand_list(args: Namespace) -> None:
    if args.listtype == "mods":
        print("List of installed mods:")
        for mod in get_mod_ids(args.instance):
            print(mod)
    elif args.listtype == "versions":
        mods_to_process = args.mod_id + get_mod_ids() if args.all else args.mod_id
        for mod in sorted(set(mods_to_process)):
            print(f"{mod}:")
            versions = get_mod_versions(mod)
            for date, subversions in sorted(versions.items()):
                firstSubversion = True
                for subver in sorted(subversions):
                    pri_ver_str = date
                    if firstSubversion:
                        firstSubversion = False
                    else:
                        pri_ver_str = (' ' * len(date))
                    ver_str = "  " + pri_ver_str + '/' + subver
                    if (date, subver) == select_latest_version(mod):
                        ver_str += ' (latest)'
                    print(ver_str)


def subcommand_activate(args: Namespace) -> None:
    deployment_directory = InstanceSettings(args.instance).get(
        ValidInstanceSettings.DEPLOYMENT_TARGET_DIR)
    if deployment_directory is None:
        from sys import stderr
        print("""
        No deployment directory has been configured for this instance. Aborting deployment.
        """.strip(), file=stderr)
        exit(1)
    mods_to_deploy: dict[str, tuple[str, str]] = {}
    for mod in get_mod_ids():
        version_to_use = select_latest_version(mod)
        if version_to_use is None:
            continue
        mods_to_deploy[mod] = version_to_use
    deploy_filesystem(deployment_directory, mods_to_deploy)


def subcommand_deactivate(args: Namespace) -> None:
    deployment_directory = InstanceSettings(args.instance).get(
        ValidInstanceSettings.DEPLOYMENT_TARGET_DIR)
    if deployment_directory is None:
        from sys import stderr
        print("""
            No deployment directory has been configured for this instance. Cannot deactivate.
        """.strip(), file=stderr)
        exit(1)
    else:
        stop_filesystem(deployment_directory)


def subcommand_import(args: Namespace) -> None:
    only_copy: bool = args.preserve_source
    raw_destination = create_mod_space(args.modid).resolve()
    destination: Path = (raw_destination / args.subdir).resolve()
    if not destination.is_relative_to(raw_destination):
        print("Subdirectories must not break out of the assigned mod folder!",
              file=stderr)
        exit(1)
    destination.mkdir(parents=True, exist_ok=True)
    source: Path = args.import_path
    if not source.is_dir():
        print("Source isn't a directory", file=stderr)
        exit(1)
    for file_or_directory in source.iterdir():
        if only_copy:
            if file_or_directory.is_file():
                copy(file_or_directory, destination)
            elif file_or_directory.is_dir():
                copytree(file_or_directory, destination)
            else:
                print(f"Unrecognized type, neither file nor directory: {str(file_or_directory)}",
                      file=stderr)
        else:
            move(file_or_directory, destination)
    recursive_lower_case_rename(raw_destination)


def subcommand_repair(args: Namespace) -> None:
    if args.repairaction == "filenamecase":
        from code.mod import base_directory
        all_mods: bool = args.all
        named_mods: list[str] = args.modids
        rename_game_files: bool = args.gamefiles
        mods_to_rename: set[str] = set(named_mods + (get_mod_ids() if all_mods else []))
        for mod in mods_to_rename:
            mod_dir = base_directory / 'mods' / mod
            recursive_lower_case_rename(mod_dir)
        if rename_game_files:
            recursive_lower_case_rename(
                instance_settings.get(ValidInstanceSettings.DEPLOYMENT_TARGET_DIR)
            )
    else:
        print("Unknown repair action", file=stderr)
        exit(1)


def get_subcommands_table() -> dict[str, Callable[[Namespace], None]]:
    return {
        "list": subcommand_list,
        "activate": subcommand_activate,
        "deactivate": subcommand_deactivate,
        "import": subcommand_import,
        "repair": subcommand_repair
    }
