<!--
Copyright header:

SPDX-License-Identifier: CC-BY-SA-4.0
SPDX-FileCopyrightText: 2023 Jonas Tobias Hopusch <git@jotoho.de>
-->

# CHANGELOG for modfs

<!--
Changelog rules:

Please attempt to follow the guidelines set by the "Keep a Changelog"
public specification.

Keep a Changelog: https://keepachangelog.com/en/1.1.0/
-->

This project adheres to the rules of semantic versioning for naming releases.

## UNRELEASED - YYYY-MM-DD

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

### Changed

- Output explanation for missing output when `list versions` is not given any mods
  ([7a48e3c](https://github.com/jotoho/modfs/commit/7a48e3c401b0c0952a49b03982faec0428d93f2c),
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

## [0.1.0] - 2023-10-02

_Initial release._

[0.1.0]: https://github.com/jotoho/tes-moddingoverlay/releases/tag/0.1.0
