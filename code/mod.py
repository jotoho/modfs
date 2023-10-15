#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from collections import OrderedDict
from pathlib import Path
from re import match, fullmatch, search
from sys import stderr
from typing import Iterable

from code.config_mod import ModConfig, ValidModSettings
from code.paths import get_meta_directory
from code.settings import get_instance_settings
from code.tools import current_date

base_directory: Path | None = None


def resolve_base_dir(base_dir: Path | None = None) -> Path:
    if base_dir is not None:
        return base_dir.resolve()
    elif base_directory is not None:
        return base_directory.resolve()
    else:
        raise ValueError("Unknown base directory")


def set_mod_base_path(base_dir: Path) -> None:
    global base_directory
    base_directory = base_dir


def get_mod_ids(base_dir: Path | None = None) -> list[str]:
    real_base_dir: Path = resolve_base_dir(base_dir)

    mod_dirs = list(filter(lambda p: p.is_dir(), (real_base_dir / 'mods').iterdir()))
    mod_ids = list(map(lambda d: d.parts[-1], mod_dirs))
    return mod_ids


def get_mod_versions(mod_id: str, base_dir: Path | None = None) -> dict[str, set[str]]:
    real_base_dir = resolve_base_dir(base_dir)
    if not mod_exists(mod_id, real_base_dir):
        raise ValueError(f"Mod {mod_id} does not exist. Cannot lookup versions.")
    mod_dir = (real_base_dir / 'mods' / mod_id).resolve()
    dated_dirs: list[Path] = list(filter(lambda p: p.is_dir(), mod_dir.iterdir()))
    results: dict[str, set[str]] = dict()
    for dated_dir in sorted(dated_dirs):
        date = dated_dir.parts[-1]
        dated_set: set[str] = results.get(date, set())
        subversion_dirs = list(filter(lambda p: p.is_dir(), dated_dir.iterdir()))
        for subversion in sorted(subversion_dirs):
            dated_set.add(subversion.parts[-1])
        results[date] = dated_set
    return results


def mod_exists(mod_id: str, base_dir: Path | None = None) -> bool:
    if base_dir is None:
        if base_directory is None:
            raise ValueError("Unknown base directory")
        else:
            base_dir = base_directory
    return (base_dir / 'mods' / mod_id).is_dir()


def validate_mod_id(mod_id: str) -> bool:
    from re import match
    return match("^[a-z0-9\\-]+$", mod_id) is not None


def has_date_version(mod_id: str) -> bool:
    return len(get_mod_versions(mod_id)) > 0


def has_subversion(mod_id: str,
                   date_version: str) -> bool:
    subversions = get_mod_versions(mod_id).get(date_version)
    return subversions is not None and len(subversions) > 0


def version_exists(mod_id: str,
                   date_version: str,
                   subversion: int | str,
                   base_dir: Path | None = None) -> bool:
    base_dir = resolve_base_dir(base_dir)
    subversion = subversion if isinstance(subversion, str) else str(subversion).zfill(2)
    version_dir = base_dir / 'mods' / mod_id / date_version / subversion
    return version_dir.is_dir()


def parse_version_tag(version_tag: str) -> tuple[str, str]:
    if fullmatch("^([0-9]{4,}-[0-9]{2}-[0-9]{2}/)?[0-9]{2}/?$", version_tag) is None:
        print("Invalid version tag. Versions need to either be a number representing today's "
              "subversion or in the format "
              "YYYY-MM-DD/XX with XX representing the subversion", file=stderr)
        exit(1)

    if fullmatch("^[0-9]{4,}-[0-9]{2}-[0-9]{2}/[0-9]{1,2}/?$", version_tag) is not None:
        version_date = match("[0-9]{4,}-[0-9]{2}-[0-9]{2}", version_tag).group(0)
        version_subversion = str(int(version_tag.split('/')[1])).zfill(2)
        return version_date, version_subversion
    elif fullmatch("^[0-9]{1,2}/?$", version_tag) is not None:
        version_date: str = current_date()
        version_subversion = str(int(version_tag)).zfill(2)
        return version_date, version_subversion
    else:
        raise ValueError(f"Error parsing version string {version_tag}")


def select_latest_version(mod_id: str,
                          base_dir: Path | None = None) -> tuple[str, str] | None:
    real_base_dir = resolve_base_dir(base_dir)
    if not mod_exists(mod_id, real_base_dir):
        raise ValueError("Mod {mod_id} does not exist")
    versions = get_mod_versions(mod_id, real_base_dir)
    list_of_dates = list(filter(lambda d: has_subversion(mod_id, d), sorted(versions.keys())))
    if len(list_of_dates) == 0:
        return None
    date = list_of_dates[-1]
    list_of_subversions = list(sorted(versions[date]))
    if len(list_of_subversions) == 0:
        return None
    subversion = list_of_subversions[-1]
    return date, subversion


def select_active_version(mod_id: str,
                          base_dir: Path | None = None) -> tuple[str, str] | None:
    saved_version_str: str = ModConfig(mod_id, base_dir).get(ValidModSettings.MOD_VERSION)
    if saved_version_str.lower() == "latest":
        return select_latest_version(mod_id, base_dir)
    else:
        return parse_version_tag(saved_version_str)


def cast_validate_mod_id(mod_id: str) -> str:
    if not validate_mod_id(mod_id):
        raise ValueError("mod id contains invalid characters")
    if mod_id not in get_mod_ids(base_directory):
        raise ValueError(f"mod {mod_id} does not exist")
    return mod_id


def get_mod_mount_path(mod_id: str, version_date: str, version_sub: str) -> Path:
    return base_directory / 'mods' / mod_id / version_date / version_sub


def mod_at_version_limit(mod_id: str, version_date: str, base_dir: Path | None = None) -> bool:
    def condition_func(s: str) -> bool:
        return (search('[^0-9]', s) is None) and int(s) >= 99

    if not mod_exists(mod_id, base_dir=base_dir):
        return False

    subversions = get_mod_versions(mod_id, base_dir=base_dir)[version_date]
    return len(list(filter(condition_func, subversions))) > 0


def create_mod_priority_list(base_dir: Path | None = None) -> None:
    prio_file = get_meta_directory(resolve_base_dir(base_dir)) / 'priority.txt'
    try:
        with open(prio_file, mode='x') as f:
            pass
    except FileExistsError:
        pass


def read_mod_priority(base_dir: Path | None = None) -> OrderedDict[str, None]:
    resolved_base_dir = resolve_base_dir(base_dir)
    prio_file = get_meta_directory(resolved_base_dir) / 'priority.txt'
    mod_order: OrderedDict[str, None] = OrderedDict()
    try:
        with (open(prio_file, mode='rt') as f):
            for read_mod_id in f.readlines():
                read_mod_id = read_mod_id.strip()
                if (len(read_mod_id) > 0
                        and validate_mod_id(read_mod_id)
                        and mod_exists(read_mod_id, resolved_base_dir)):
                    mod_order[read_mod_id] = None
    except FileNotFoundError:
        pass
    for mod_id in get_mod_ids():
        if mod_id not in mod_order.keys():
            mod_order[mod_id] = None
    return mod_order


def write_mod_priority(mod_order: OrderedDict[str, None], base_dir: Path | None = None) -> None:
    prio_file = get_meta_directory(resolve_base_dir(base_dir)) / 'priority.txt'
    with open(prio_file, mode='wt') as f:
        for mod_id in mod_order.keys():
            f.write(mod_id + '\n')


def build_mod_order(order_template: Iterable[str]) -> OrderedDict[str, None]:
    final_mod_order = OrderedDict()
    for mod in order_template:
        if mod not in final_mod_order.keys():
            final_mod_order[mod] = None
    return final_mod_order


def parse_mod_conflicts() -> dict[frozenset[str], set[Path]]:
    mod_dirs: set[Path] = set()
    for mod_id in get_mod_ids():
        version_tuple = select_active_version(mod_id)
        if version_tuple is None:
            continue
        date, sub = version_tuple
        mod_dirs.add(get_mod_mount_path(mod_id, date, sub))
    file_mapping: dict[Path, set[str]] = dict()
    for mod_dir in mod_dirs:
        for found_path in mod_dir.rglob("*"):
            if found_path.is_file():
                found_path = found_path.relative_to(mod_dir)
                if found_path in file_mapping.keys():
                    file_mapping[found_path].add(mod_dir.parts[-3])
                else:
                    file_mapping[found_path] = {mod_dir.parts[-3]}
    mod_mapping: dict[frozenset[str], set[Path]] = dict()
    for path, mod_set in file_mapping.items():
        if len(mod_set) < 2:
            continue
        frozen_mod_set = frozenset(mod_set)
        if frozen_mod_set in mod_mapping.keys():
            mod_mapping[frozen_mod_set].add(path)
        else:
            mod_mapping[frozen_mod_set] = {path}
    return mod_mapping
