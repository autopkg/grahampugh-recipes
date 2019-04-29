# Parallels Desktop

Creates an installable package for Parallels Desktop. This is done with the help of the `pd-autodeploy` file obtained from the Parallels website.

There is no download recipe since Parallels Desktop is not publicly available.

Requires running as:

    autopkg run --pkg /path/to/downloaded-parallels.dmg ParallelsDesktop.pkg

You must override the `LICENSE_KEY`.

It is also possible to override the software update settings. See `ParallelsDesktopPackager.py` for details.
