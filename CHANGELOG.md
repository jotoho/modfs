<!--
Copyright header:

SPDX-License-Identifier: CC-BY-SA-4.0
SPDX-FileCopyrightText: 2023-2024 Jonas Tobias Hopusch <git@jotoho.de>
-->

# CHANGELOG for modfs

<!--
Changelog rules:

Please attempt to follow the guidelines set by the "Keep a Changelog"
public specification.

Keep a Changelog: https://keepachangelog.com/en/1.1.0/
-->

This project adheres to the rules of semantic versioning for naming releases.

## [1.0.0] - 2024-06-13

### Added

- Support custom mod loading order
  ([7a48e3c](https://github.com/jotoho/modfs/commit/7a48e3c401b0c0952a49b03982faec0428d93f2c),
  [@jotoho](https://github.com/jotoho))
- Add mechanism for developer debugging commands with subcommand for creating empty new mods
  ([7a48e3c](https://github.com/jotoho/modfs/commit/7a48e3c401b0c0952a49b03982faec0428d93f2c),
  [@jotoho](https://github.com/jotoho))
- Add list subcommand to show potential file conflicts between current mods
  ([1c8082a](https://github.com/jotoho/modfs/commit/1c8082ac5f6c2a2f7f27fd1d8c52e2239bdae363),
  [@jotoho](https://github.com/jotoho))
- Add configuration subcommand for managing instance-level settings
  ([a39444b](https://github.com/jotoho/modfs/commit/a39444b1527d7e63e01574cb122bbf8cf6a4aa37),
  [@jotoho](https://github.com/jotoho))
- Add `delete` subcommand for deleting installed mods
  ([652da53](https://github.com/jotoho/modfs/commit/652da53a930388218464ced374dd7f0caa535b00),
  [@jotoho](https://github.com/jotoho))
- Add ability to suspend (enable/disable) mods from being loaded.
  See `enable` / `disable` subcommands.
  ([83c220c](https://github.com/jotoho/modfs/commit/83c220ce939f6cd19ef7b63aa896bb60d3f1f8e1),
  [@jotoho](https://github.com/jotoho))
- Add `status` subcommand.
  Currently, it only informs the user whether the filesystem is active, or not.
  More information may be added in the future.
  ([bbf8fc1](https://github.com/jotoho/modfs/commit/bbf8fc104d03cd764c603d902de2877849cc8b8e),
  [@jotoho](https://github.com/jotoho))
- Add ability to overwrite automatic latest version selection.
  Users can now, on a per-mod basis, instruct modfs to load a specific version instead of the most
  recently installed. This can be useful for troubleshooting.
  See `useversion` subcommand for details. Specify `latest` as version to return to automatic mode.
  ([856eddc](https://github.com/jotoho/modfs/commit/856eddc681bfd5829c2fd0ed4f8aa032c4b551e8),
  [@jotoho](https://github.com/jotoho))
- Add mod-specific metadata storage.
  Users can now view and store additional information about a mod, like the author,
  the mod name (less restrictive than mod id), the URL of the mod page and custom text notes.
  See `mod` subcommand for details.
  ([fc22160](https://github.com/jotoho/modfs/commit/fc22160c06d0e3b4ccc3410d28b848c12faa5c94),
  [@jotoho](https://github.com/jotoho))
  ([74c43e4](https://github.com/jotoho/modfs/commit/74c43e4188a285461c35ffe450bc019807f7d183),
  [@jotoho](https://github.com/jotoho))
- Experimental support for directly importing from archive files.
  THIS FEATURE IS LARGELY UNTESTED AT THIS TIME - use at your own risk!
  ([71dfc45](https://github.com/jotoho/modfs/commit/71dfc45cc018fc9539c0dc702497fe835ce85be7),
  [@jotoho](https://github.com/jotoho))
- Import command can now directly set or update mod metadata.
  ([eb6633d](https://github.com/jotoho/modfs/commit/eb6633d28e432c4160cfed1bb112d6dcdf3fc57d),
  [@jotoho])
- Allow `repair filenamecase` to also process overflow, if passed `--overflow` commandline argument.
  ([9a38143](https://github.com/jotoho/modfs/commit/9a38143c8d99f07e1658cc6de62b12d045624cb8),
  [@jotoho](https://github.com/jotoho))
- Added symbolic link `m̀odfs` to `modfs.py`.
  This is intended to make using modfs less painful, if the application root directory is in PATH.
  For example, `m̀odfs.py status` can now also be called via `m̀odfs status`.
  ([a51ba79](https://github.com/jotoho/modfs/commit/a51ba79cd942a5d6fec412524f20950fe8bcdf7f),
  [@jotoho])
- The forced case-standardization via renaming can now be disabled instance-wide using
  the `suppressLowercaseRenaming` instance setting.
  ([0292ed4](https://github.com/jotoho/modfs/commit/0292ed409889fc6813844ad24cc10de61df358ea),
  [@jotoho](https://github.com/jotoho))
- Support placeholder substitution in import subdir string.
  The placeholder `MOD_NAME` will be replaced with the mod id.
  The placeholder `SRC_DIR` will be replaced with the name of the import source folder - this is
  important for use-cases like ESO Addons.
  ([0292ed4](https://github.com/jotoho/modfs/commit/0292ed409889fc6813844ad24cc10de61df358ea),
   [0996afc](https://github.com/jotoho/modfs/commit/0996afce3c1770a1046f046bf75d33252529c1dc),
   [@jotoho](https://github.com/jotoho))
- modfs will now track when a mod was last checked for updates.
  The stored timestamp will be updated when a new version is imported or when signalled a lack of
  newer versions via `markuptodate`.
  The list of mods, sorted by their last update check, can be shown by using the `list updatecheck`
  command. It also supports a commandline flag to exclude mods updated on the current day.
  ([7431d08](https://github.com/jotoho/modfs/commit/7431d081119ebc689dc35f605d459d68a72c1f33),
  [e2405db](https://github.com/jotoho/modfs/commit/e2405db7cc34195c8295abf3f8f270ee2412fbab),
  [@jotoho](https://github.com/jotoho))

### Changed

- Output explanation for missing output when `list versions` is not given any mods
  ([7a48e3c](https://github.com/jotoho/modfs/commit/7a48e3c401b0c0952a49b03982faec0428d93f2c),
  [@jotoho](https://github.com/jotoho))
- Instance config directory changed from `.moddingoverlay` to `.modfs`.
  To aid in the transition, the old directory will still be read, if no directory with the new name
  can be found.
  This transition mechanism may be removed in a future update. Users are recommended to rename their
  `.moddingoverlay` directories.
  ([eb60900](https://github.com/jotoho/modfs/commit/eb60900d11ad2dd27a6c223b61359ea8af7129a9),
  [@jotoho](https://github.com/jotoho))
- `init` command now automatically performs case-standardization on game files.
  ([c20f760](https://github.com/jotoho/modfs/commit/c20f76074ad9f334a20ee0a234a536267aa0a744),
  [@jotoho](https://github.com/jotoho))
- Instance settings storing paths are now stored in relative form, if possible.
  This is intended to make moving the instance directory easier.
  ([9cecca2](https://github.com/jotoho/modfs/commit/9cecca2d0073c8d6c1f7780d153ed48c05f7fc7e),
  [@jotoho](https://github.com/jotoho))
- Hardcoded placeholders in subdir strings can now be automatically replaced - see `Added` section
  for details.

### Removed

- Unused instance setting `BACKGROUND_DEPLOYMENT`/`deployInBackground` was removed in this version.
  No user action is required.
  ([1e901be](https://github.com/jotoho/modfs/commit/1e901be1e39eb5114b3a4843422880b88e9800d2),
  [@jotoho](https://github.com/jotoho))

### Fixed

- Create new mods beginning at `00` instead of `01`
  ([679231d](https://github.com/jotoho/modfs/commit/679231d5d6aa2880338418c910f6dcfcc3f240e4),
  [@jotoho](https://github.com/jotoho))
- Detect and abort when user attempts to create more subversions than supported
  ([dd0166c](https://github.com/jotoho/modfs/commit/dd0166c4e8c90389aa0c22efd03478a795455d94),
  [@jotoho](https://github.com/jotoho))
- Fixed global instance settings always being None
  ([4c944cc](https://github.com/jotoho/modfs/commit/4c944cc22b6587ee22e23422bdd4a83ea200bef1),
  [@jotoho](https://github.com/jotoho))
- Fix instance setting issues:
  Files containing value `0` were previously misidentified as meaning `True`, instead of `False`.
  ([81122dc](https://github.com/jotoho/modfs/commit/81122dcfaf5c29a7af0cab1699fa33c8f6ec42d9),
  [@jotoho](https://github.com/jotoho))
- Some mandatory command arguments were previously not marked as required, causing potential issues.
  ([1bc7c72](https://github.com/jotoho/modfs/commit/1bc7c720ae4848a5bfa3e4184569cae3f414170a),
  [@jotoho](https://github.com/jotoho))
- Resolved issue concerning failure to import a mod which did not have previous versions installed.
  Unsure if this bug was in `0.1.0` - noting to be thorough.
  ([a737148](https://github.com/jotoho/modfs/commit/a73714876ccf5858cca894d16a692e23821bb632),
  [@jotoho](https://github.com/jotoho))
- Fixed issues with filesystem deployment when using `--instance` to set the instance directory,
  instead of defaulting to the working directory.
  ([54a6e2a](https://github.com/jotoho/modfs/commit/54a6e2aa1479d6d388cd81d09b1db08fc290c8f1),
  [@jotoho])
- Copying system used when calling `ìmport` with `--preserve-source` was defective.
  Additionally, files and directories stored in direct subdirectories of the source directory,
  would falsely be placed directly into the destination directory due to a programming error.
  ([d251c0f](https://github.com/jotoho/modfs/commit/d251c0fa755ebe17cd4fd8865f158fd4a16f4545),
  [@jotoho])

## [0.1.0] - 2023-10-02

_Initial release._

[0.1.0]: https://github.com/jotoho/tes-moddingoverlay/releases/tag/0.1.0
