#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from pathlib import Path
from sys import stderr

from code.mod import resolve_base_dir, select_latest_version


def current_date() -> str:
    from datetime import date
    return date.today().isoformat()


def create_mod_space(mod_id: str, base_dir: Path | None = None) -> Path:
    real_base_dir = resolve_base_dir(base_dir)
    mod_dir = real_base_dir / 'mods' / mod_id
    mod_dir.mkdir(parents=True, exist_ok=True)
    version_tuple = select_latest_version(mod_id)
    prev_date, prev_subversion = version_tuple if version_tuple is not None else (None, None)
    if prev_date == current_date():
        new_subversion = str(int(prev_subversion) + 1).zfill(2)
        location = mod_dir / prev_date / new_subversion
        location.mkdir(parents=True, exist_ok=True)
        return location
    else:
        location: Path = mod_dir / current_date() / '01'
        location.mkdir(parents=True, exist_ok=True)
        return location


def recursive_lower_case_rename(current_path: Path) -> None:
    if current_path is None or not isinstance(current_path, Path) or not current_path.is_dir():
        return

    # print("Processing all entries in directory: " + str(currentPath))
    for element in current_path.iterdir():
        if element.exists() and (element.is_dir() or element.is_file()):
            new_path = Path(
                current_path.joinpath(Path(str(element.relative_to(current_path)).lower())))
            if new_path.exists():
                if new_path.samefile(element):
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
            print("FATAL: for loop emitted invalid path!", file=stderr)
            from errno import EIO
            exit(EIO)
    for element in current_path.iterdir():
        if element.is_dir():
            recursive_lower_case_rename(element)
