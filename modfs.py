#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from pathlib import Path
from sys import stderr

from code.commandline import process_commandline_args, get_instance_path
from code.mod import set_mod_base_path, resolve_base_dir
from code.settings import set_instance_settings, InstanceSettings, get_instance_settings
from code.subcommands import get_subcommands_table, SubcommandArgDict


def app_install_dir() -> Path:
    return Path(__file__).resolve(strict=True).parent


def execution_path_dir() -> Path | None:
    from shutil import which
    from sys import argv
    if len(argv) > 0:
        script_path_str = which(argv[0])
        if script_path_str is not None:
            script_path = Path(script_path_str)
            if script_path.exists():
                return script_path.resolve(strict=True).parent
    return None


def get_git_version(working_dir: Path) -> str:
    from subprocess import run, PIPE, DEVNULL
    from os import getcwd, chdir
    previous_working_dir = getcwd()
    result = run(["git", "describe", "--tags", "--always", "--dirty"],
                 stdout=PIPE, stderr=DEVNULL, cwd=working_dir)
    chdir(previous_working_dir)
    return result.stdout.decode().strip()


def main() -> None:
    instance_path: Path = get_instance_path()
    set_mod_base_path(instance_path)
    assert resolve_base_dir(base_dir=None) is not None
    set_instance_settings(InstanceSettings(instance_path))
    assert get_instance_settings() is not None
    # Warning: mod base path must be known before this can be safely called
    args: SubcommandArgDict = vars(process_commandline_args())
    if args["show_args"]:
        from pprint import pprint
        pprint(vars(args))

    exec_dir = execution_path_dir()
    args["version_string"] = get_git_version(exec_dir
                                             if exec_dir is not None
                                             else app_install_dir())
    subcommands = get_subcommands_table()
    if args["subcommand"] in subcommands:
        subcommands[args["subcommand"]](args)
    else:
        print(f"ERROR: No action has been implemented for subcommand {args['subcommand']}.",
              "This is either a bug or a missing feature!", file=stderr)
        exit(1)


if __name__ == "__main__":
    main()
