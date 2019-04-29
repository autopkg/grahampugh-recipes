# JMP

There is no download recipe since JMP is not publicly available. Therefore you must specify a path to the package which must be obtained manually.

Creates a package from a pre-downloaded JMP installer which has already been installed on a client, and the SIP file converted to a `JMP.per` file as per the instructions in the JMP Deployment Guide. The pre-installed app should then be placed in a DMG for use by this recipe.

You need to manually supply the JMP version, since attempts to extract this from the installer have so far failed.

Run as:

    autopkg run --pkg /path/to/downloaded-JMP.dmg JMP.pkg
