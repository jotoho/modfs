#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from argparse import Namespace
from collections import OrderedDict
from pathlib import Path
from shutil import copy, move, copytree
from sys import stderr
from typing import Callable, Literal

from code.creation import create_mod_space, recursive_lower_case_rename, ask_for_path, current_date
from code.deployer import deploy_filesystem, stop_filesystem, are_paths_on_same_filesystem, \
    is_fuse_overlayfs_mounted
from code.mod import get_mod_ids, get_mod_versions, select_latest_version, validate_mod_id, \
    mod_at_version_limit, write_mod_priority, read_mod_priority, build_mod_order, \
    parse_mod_conflicts
from code.settings import InstanceSettings, ValidInstanceSettings, instance_settings, \
    get_instance_settings


def subcommand_list(args: Namespace) -> None:
    if args.listtype == "mods":
        print("List of installed mods:")
        for mod in get_mod_ids(args.instance):
            print(mod)
    elif args.listtype == "versions":
        if not args.all and len(args.mod_id) == 0:
            print("You need to specify mods or give the --all flag to list versions.",
                  file=stderr)
            exit(1)
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
    elif args.listtype == "priority":
        for mod_id in read_mod_priority().keys():
            print(mod_id)
    elif args.listtype == "conflicts":
        for mods, files in parse_mod_conflicts().items():
            print(set(mods))
            for file in files:
                print((" " * 4) + str(file))


def subcommand_activate(args: Namespace) -> None:
    deployment_directory = InstanceSettings(args.instance).get(
        ValidInstanceSettings.DEPLOYMENT_TARGET_DIR)
    if deployment_directory is None:
        from sys import stderr
        print("""
        No deployment directory has been configured for this instance. Aborting deployment.
        """.strip(), file=stderr)
        exit(1)
    mods_to_deploy: OrderedDict[str, tuple[str, str]] = OrderedDict()
    for mod in read_mod_priority().keys():
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
    mod_id: str = args.modid
    if not validate_mod_id(mod_id):
        print("A mod id may only contain lower case letters a-z, digits 0-9 and the minus sign",
              file=stderr)
        exit(1)

    if mod_at_version_limit(mod_id, current_date(), args.instance):
        print("A mod may only have 100 subversions per day (00-99). Aborting import.",
              file=stderr)
        stderr.flush()
        exit(1)
    else:
        print(f"Importing mod {mod_id}")

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
    elif args.repairaction == "filepriority":
        write_mod_priority(read_mod_priority())
    else:
        print("Unknown repair action", file=stderr)
        exit(1)


def subcommand_init(args: Namespace) -> None:
    from code.settings import instance_settings
    instance_settings.initialize_settings_directory()
    (args.instance / 'mods').mkdir(exist_ok=True, parents=True)
    write_mod_priority(read_mod_priority(base_dir=args.instance), base_dir=args.instance)

    target_directory = ask_for_path(
        "Please specify the directory to deploy the mods of this instance to",
        lambda path: path.is_dir())

    overflow_directory = ask_for_path(
        "Please specify an overflow directory for modified files",
        lambda path: path.is_dir())

    work_directory = ask_for_path(
        "Please specify a working directory on the same filesystem as the target directory",
        lambda path: path.is_dir() and are_paths_on_same_filesystem(path, target_directory))

    instance_settings.set(ValidInstanceSettings.DEPLOYMENT_TARGET_DIR, target_directory)
    instance_settings.set(ValidInstanceSettings.FILESYSTEM_OVERFLOW_DIR, overflow_directory)
    instance_settings.set(ValidInstanceSettings.FILESYSTEM_WORK_DIR, work_directory)


def subcommand_reorder(args: Namespace) -> None:
    if is_fuse_overlayfs_mounted():
        print("You cannot reorder mods while the filesystem is active!",
              file=stderr)
        exit(1)

    type_operation = Literal["before", "after", "highest", "lowest"]
    reorder_operation: type_operation | None = args.reorder_operation
    mod_id_to_reorder: str = args.mod_to_reorder
    if reorder_operation in {"after", "before"}:
        reference_modid: str | None = args.reference_modid
        if reference_modid is None:
            print("No reference for reordering specified.",
                  file=stderr)
            exit(1)

        mod_order = list(read_mod_priority().keys())

        if mod_id_to_reorder not in mod_order:
            print("mod to reorder does not exist",
                  file=stderr)
            exit(1)
        elif reference_modid not in mod_order:
            print("reference mod does not exist",
                  file=stderr)
            exit(1)

        if reorder_operation == "after":
            mod_order.remove(mod_id_to_reorder)
            index = mod_order.index(reference_modid)
            mod_order = mod_order[:index + 1] + [mod_id_to_reorder] + mod_order[index + 1:]
        elif reorder_operation == "before":
            mod_order.remove(mod_id_to_reorder)
            index = mod_order.index(reference_modid)
            mod_order = mod_order[:index] + [mod_id_to_reorder] + mod_order[index:]

        write_mod_priority(build_mod_order(mod_order))
    elif reorder_operation in {"highest", "lowest"}:
        mod_order = read_mod_priority()
        if reorder_operation == "highest":
            if mod_id_to_reorder in mod_order.keys():
                mod_order.move_to_end(mod_id_to_reorder, last=True)
            else:
                print(f"Mod {mod_id_to_reorder} does not exist.",
                      file=stderr)
        elif reorder_operation == "lowest":
            if mod_id_to_reorder in mod_order.keys():
                mod_order.move_to_end(mod_id_to_reorder, last=False)
            else:
                print(f"Mod {mod_id_to_reorder} does not exist.",
                      file=stderr)
        write_mod_priority(mod_order)
    else:
        print("reorder operation has not been specified. See --help for more info.",
              file=stderr)
        exit(1)


def subcommand_developer(args: Namespace) -> None:
    no_dev_warning: bool = get_instance_settings().get(
        ValidInstanceSettings.SUPPRESS_DEVELOPER_CMD_WARNING)
    if not no_dev_warning:
        print("""
YOU ARE EXECUTING A DEVELOPER SUBCOMMAND.
These features are exclusively meant for debugging and may cease working at any time
or even cause permanent damage.
Do not use them unless you know what you're doing or are following instructions by a developer.
    """.strip())

    action: str | None = args.developer_action
    if action == "create-blank-mod":
        print("Created directory:", create_mod_space(args.mod_id))


def get_subcommands_table() -> dict[str, Callable[[Namespace], None]]:
    return {
        "list": subcommand_list,
        "activate": subcommand_activate,
        "on": subcommand_activate,
        "deactivate": subcommand_deactivate,
        "off": subcommand_deactivate,
        "import": subcommand_import,
        "repair": subcommand_repair,
        "init": subcommand_init,
        "reorder": subcommand_reorder,
        "developer": subcommand_developer
    }
