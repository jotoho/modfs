<!-- 
Copyright 2023 Jonas Tobias Hopusch <git@jotoho.de>
SPDX-License-Identifier: AGPL-3.0-only
-->
# Design notes on the instance directory structure
Inside the database folder (referred to as "root" folder, from here), all the information needed to
operate a particular usage-instance of the application is stored, including mods, configuration and required
metadata.

## .moddingoverlay/
### settings/
This directory will contain a file for each setting set or defined for this instance.
These files will contain their respective values for the setting.

### modpriority.txt
An LF-delimited list of mod ids in decreasing priority.
At every point in time, the set of mod ids should match the set of mods installed.

### compatibilityversion.txt
Contains the integer representing the major version 

## mods/
### &lt;modid&gt;/
The unique id of this mod.
Mod ids, while chosen by the user, can only be composed of a limited set of
letters.

#### &lt;version date component (YYYY-MM-DD)&gt;/
Represents the day on which the mod was installed.

##### &lt;version fallback counter component (00-99)&gt;/
Name represents the iteration of the mod on the day of installation and contains
the files of the mod.

Begins with 00 and ends at 99. There cannot be more than one hundred versions
in a single day. *(Who would do that anyway?)*

##### &lt;version fallback counter component (00-99)&gt;.json
Can contain:
 - Alternative version name (such as the version number defined by the author)
 - Notes

### &lt;modid&gt;.json
Can contain:
 - the pretty name of the mod 
   (fancy display name - can be more complex than mod id)
   <br/>default: none
 - boolean switch that disables the mod
   (a deactivated mod will not be loaded into the filesystem)
   <br/>default: mod enabled
 - an override for the version that will be loaded
   <br/>default: none (loads the latest version)
 - author name
   <br/>default: none
 - Notes 
   <br/>default: none
