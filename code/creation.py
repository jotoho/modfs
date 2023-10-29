#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from filecmp import cmp
from pathlib import Path
from pprint import pprint
from re import IGNORECASE, compile, Pattern
from shutil import copy, copytree, move, which
from subprocess import run
from sys import stderr
from typing import Callable

from code.mod import resolve_base_dir, select_latest_version
from code.tools import current_date


def create_mod_space(mod_id: str, base_dir: Path | None = None) -> Path:
    mod_dir = resolve_base_dir(base_dir) / 'mods' / mod_id
    mod_dir.mkdir(parents=True, exist_ok=True)
    version_tuple = select_latest_version(mod_id)
    if version_tuple is not None:
        prev_date, prev_subversion = version_tuple
        if prev_date == current_date():
            new_subversion = str(int(prev_subversion) + 1).zfill(2)
            location = mod_dir / prev_date / new_subversion
            location.mkdir(parents=True, exist_ok=True)
            return location

    location: Path = mod_dir / current_date() / '00'
    location.mkdir(parents=True, exist_ok=True)
    return location


def recursive_lower_case_rename(current_path: Path) -> None:
    if current_path is None or not isinstance(current_path, Path) or not current_path.is_dir():
        return

    # print("Processing all entries in directory: " + str(currentPath))
    for element in current_path.iterdir():
        if element.exists():
            new_path = Path(
                current_path.joinpath(Path(str(element.relative_to(current_path)).lower())))
            if new_path.exists():
                if new_path.samefile(element):
                    continue
                elif cmp(element, new_path, shallow=False):
                    element.unlink(missing_ok=True)
                    continue
                else:
                    print(f"Path '{str(new_path)}' is already used. Cannot move '{str(element)}'",
                          file=stderr)
                    continue
            else:
                assert element.exists()
                assert element.is_dir() or element.is_file()
                element.rename(new_path)
        else:
            print("FATAL: for loop emitted invalid path!",
                  file=stderr)
            from errno import EIO
            exit(EIO)
    for element in current_path.iterdir():
        if element.is_dir():
            recursive_lower_case_rename(element)


def ask_for_path(prompt: str, meets_requirements: Callable[[Path | None], bool]) -> Path:
    deployment_target_dir: Path | None = None
    first_input: bool = True
    while deployment_target_dir is None or not meets_requirements(deployment_target_dir):
        if first_input:
            first_input = False
        else:
            print("\nYour previous input is invalid. Please try again.")

        print(prompt)

        try:
            deployment_target_dir = Path(input("Path: ")).resolve()
        except EOFError:
            print("FATAL: User closed the standard input stream", file=stderr)
            from os import EX_NOINPUT
            exit(EX_NOINPUT)
        except (TypeError, ValueError):
            pass
    return deployment_target_dir


def transfer_mod_files(source_dir: Path, destination_dir: Path, only_copy: bool) -> None:
    for file_or_directory in source_dir.iterdir():
        if only_copy:
            if file_or_directory.is_file():
                copy(file_or_directory, destination_dir)
            elif file_or_directory.is_dir():
                copytree(file_or_directory, destination_dir)
            else:
                print(f"Unrecognized type, neither file nor directory: {str(file_or_directory)}",
                      file=stderr)
        else:
            move(file_or_directory, destination_dir)


def extract_archive(archive_file: Path, destination_dir: Path) -> None:
    extract_commands: dict[Pattern, Callable[[Path, Path], list[str]]] = {
        compile(r".tar(\.[a-z]+){,1}$", flags=IGNORECASE): (lambda a, d: ["tar", "-x",
                                                                          "-f", str(a),
                                                                          f"--one-top-level={d}"]),
        compile(r".zip$", flags=IGNORECASE): (lambda a, d: ["unzip", "-d", str(d), str(a)]),
        compile(r".rar$", flags=IGNORECASE): (lambda a, d: ["unrar", "x", str(a), str(d)]),
        compile(r".7z$", flags=IGNORECASE): (lambda a, d: ["7z", f"-o{d}", str(a)]),
    }

    def filter_commands(key: Pattern) -> bool:
        return key.search(archive_file.parts[-1]) is not None

    if len(set(destination_dir.iterdir())) != 0:
        ValueError("destination directory is not empty")

    matching_commands = list(filter(filter_commands, extract_commands.keys()))

    if len(matching_commands) < 1:
        raise ValueError(f"Archive file type of '{archive_file}' is not supported")

    command = extract_commands[matching_commands[0]](archive_file, destination_dir)
    if which(command[0]) is not None:
        run(command)
    else:
        raise f"extraction dependency {command[0]} is not installed"
