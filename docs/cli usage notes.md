<!-- 
Copyright 2023 Jonas Tobias Hopusch &lt;git@jotoho.de&gt;
SPDX-License-Identifier: AGPL-3.0-only
-->
# CLI commandline arguments
and their uses within moddingoverlay.

## modfs.py
### init
Initialize current (empty) directory with the structure and information needed to
manage a set of mods and deploy them.

 -  `--installhelper=<yes | no>` Whether a python file should be created,
    which redirects commands to this installation of the modding overlay 

### config
#### get &lt;settingid&gt;
#### set &lt;settingid&gt; &lt;value&gt;
#### unset &lt;settingid&gt;

### status
Shows whether the overlay filesystem of this instance is currently active
and some basic statistics.

### activate
Mounts the overlay filesystem for this instance, 
which temporarily merges mods into the game data. 

Many other commands are unavailable while the overlay filesystem is mounted.

### on

Alias of `activate` subcommand.

### deactivate
Unmounts the overlay filesystem for this instance.

### off
Alias of `deactivate` subcommand.

### import
Expects the path of the directory to import as an argument.

### delete &lt;modid&gt; [version]

### list
#### mods
Shows list of all installed mods in order of decreasing priority.

#### versions &lt;modid&gt;
Lists the installed versions of the specified mod.

### useversion &lt;modid&gt; (latest | "YYYY-MM-DD[/PP]")
Switches the mod in question to use the specified version.
Specifying `latest` 

### reorder
Runs subcommand `repair filepriority` and then opens the mod priority list in the
user's editor.

### repair
#### filepriority
Removes mods from the priority list that no longer exist in the database
and then appends installed mods not found in the file.

#### filenamecase
Renames files and directories belonging to the given mod(s) into their lower-case equivalents.
This is to avoid the possiblity of case-sensitive filesystems on Linux causing trouble.

 - With `--all` flag, it will process all known mods
 - Otherwise, the command operates on the given space-delimited list of mod ids.

### [help | -h | --help [subcommand]]

Show the most basic information on this application
and a list of subcommands and options that can be used.
