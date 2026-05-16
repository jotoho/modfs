#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023-2026 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path
from argparse import ArgumentParser
from os import getcwd

def get_instance_path() -> Path:
    # Create a parser just for the early value
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--instance",
                        type=Path,
                        default=Path(getcwd()),
                        help="The instance to run your commands on. Defaults to current working "
                             "directory.")
    args, _ = parser.parse_known_args()
    return args.instance
