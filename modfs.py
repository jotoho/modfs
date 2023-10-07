#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from pathlib import Path
from sys import stderr

from code.commandline import process_commandline_args, get_instance_path
from code.mod import set_mod_base_path, resolve_base_dir
from code.settings import set_instance_settings, InstanceSettings, get_instance_settings
from code.subcommands import get_subcommands_table


def main() -> None:
    instance_path: Path = get_instance_path()
    set_mod_base_path(instance_path)
    assert resolve_base_dir(None) is not None
    set_instance_settings(InstanceSettings(instance_path))
    assert get_instance_settings() is not None
    # Warning: mod base path must be known before this can be safely called
    args = process_commandline_args()
    if args.show_args:
        from pprint import pprint
        pprint(vars(args))

    subcommands = get_subcommands_table()
    if args.subcommand in subcommands:
        subcommands[args.subcommand](args)
    else:
        print(f"ERROR: No action has been implemented for subcommand {args.subcommand}.",
              "This is either a bug or a missing feature!", file=stderr)
        exit(1)


if __name__ == "__main__":
    main()
