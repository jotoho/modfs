#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
# SPDX-License-Identifier: AGPL-3.0-only
from pathlib import Path

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


def cast_validate_mod_id(mod_id: str) -> str:
    if not validate_mod_id(mod_id):
        raise ValueError("mod id contains invalid characters")
    if mod_id not in get_mod_ids(base_directory):
        raise ValueError(f"mod {mod_id} does not exist")
    return mod_id


def get_mod_mount_path(mod_id: str, version_date: str, version_sub: str) -> Path:
    return base_directory / 'mods' / mod_id / version_date / version_sub
