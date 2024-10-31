#!/usr/local/autopkg/python

# -*- coding: utf-8 -*-
#
# Copyright 2022 Matthew Warren
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
IconGenerator

This is a processor for AutoPkg, adapted from AppIconExtractor by Matthew Warren:
https://github.com/autopkg/haircut-recipes/blob/master/Processors/AppIconExtractor.py

Important! You *must* install the Pillow library to AutoPkg's Python framework.
You can do this by running:

/usr/local/autopkg/python -m pip install --upgrade Pillow
"""

import binascii
import plistlib
import base64
import io
import os

from pathlib import Path
from autopkglib import ProcessorError  # pylint: disable=import-error
from autopkglib.DmgMounter import DmgMounter  # pylint: disable=import-error

try:
    from PIL import Image
except (ImportError, ModuleNotFoundError) as ex:
    raise ProcessorError(
        "The Pillow library is required, but was not found. "
        "Please run the following command to install the library: "
        "/usr/local/autopkg/python -m pip install --upgrade Pillow"
    ) from ex

__all__ = ["IconGenerator"]


# Default icon strings
DEFAULT_ICON_UPDATE = "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"  # pylint: disable=line-too-long
DEFAULT_ICON_INSTALL = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAFZElEQVR4nO2be0yVdRjHn3O0mXlHwEslgjeWt3nJYSoe0azV1lZbdy8laho1tVx3t/7IZTfmCNRKliOzjdXWVqtFgICURc1MMiJuGiMF0RSIFeE5fZ73BIcXMGid8xbnPR/22fP8zplyfl/e83vf97zvcUgvSCy643JKHI7F0X85BrWq2odhr/4/P+DBJmzEBmyrNXgI89PnZZZRe+SSL5hJ63MLcRXejsOwL3EK8zGNMAqp3eLALjD5CMp+XI59HTem4pME0Uw10SUAJr+YcgB1cw8mKnANIRRQ2zEFwOQTKFnYD4MRDy4jhFyqQXsATF4Xs6M4CoOZKpxOCL9SvQEweSclG5egHUglgIep7QEsp3yCdsGDLkIoaAsgg7IS7UQmAdzpYPKDGNSiVjtxmgDGaAB22/w7MkUDWE2zT+zJOg3gcZodaEcyNIBkmi1oR7I1gAM0d6MdKdIAcmgS0I6UaADHaa5BS4kaFCMLw13i9rilsD5PqptPyH9AjQZQTzMSLeOqgePk2Wkv0Xnx8PNM8Rap/U1P4S2lQQNw0xhHhFZxb1SiLIlcTucj6/SHkln9Fp2luDUAD42lbJ2yTWKHTqPzcez8EUkpe4HOWkIBhAIIBRAKIBQA1VJCAYQCCAUQCiAUQCiAIAxg0pBYuXnMrRI+IEJya7Ok4Ey2tHpaecbMPwmgv+MycUVeb5w96unyR6fel/KmUp7xD34LwMHP9hk7JXKAXmL0cuSXItlTsZMPPS4y8tHbAPo5+knSxK0yY/hsRl40BP3sQD9D8Ad+C0D/6jtm6GV4M1+eLZS9lam8XN+v2TL5KZk6bCadDw1rV/krdF6cDqc8MGGTzBkRx8jMY98mybmWerp/j98CULZN3SFRV0TTmTl0JlcyTrxOBN5f9eDER2X2iHl0Pg6fLZD0yjQ6XhQ/iTFJEjdyESMzFU0/yvMl2+j8g18D0M168+QnjPdtZ3JqP5Z3ftonyproJLkuPJ7OR17dp7L/5F46LlKOXyeLI5bRmWlx/y7Jpdv/n2tAG9OHzZKkSVsJoT8jM2+fTJeDdVmygo/EXCxqHWn7SGzZqJvkrnGrecRMi7vFWCN+aPiOkf/wewDKzOFzjM1cF7GOXGQxTC59TqYPnyU3jr6FR3x88PO7UtpYIo+wPjg7/btWzx/yatmLcvzCMUb+JSABKPoe3zBhc5fJNLY2GCv+gnCXdCSPLWNu2HwZ3H8IIx+6G00re1mKL3zDyP8ELABlblicrI/ZRAhORj50MdSFriPdPaZbzO7yZDl6/mtGgSGgASjzwhbI2piHuoTQE3rsoMcQunsMJAEPQNHdme7WOv+FL4VeLXqjMkW+OneYUWCxJABF3/P3RW8ggr8PQd8K6Rw4fcEBlBVYFoCyKCJBVo1fTwTdh6CTf7Nqt3xen8/IGjQAt1a0BD2xWRG1ls6MTl6PFvWo0UKMS2MNNOZ9T4BZEnmD3BN1P6l7c9fJ60GSHg1ajHFxtIZmLFpK7NCpEh++lKl7OG3O4SDoex61HOPyeAlNLNoR4wYJ3dFei3bEuEUmm2Yp2hHjJqkMmpVoR4zb5NbTvIZ2ZJ0GoAugLoR2ZIqxIyaEOkoE2gnvzdI0GsB7lNvQTnhvl6fRAFwiosegxtgG6PmP7wsTCiHsomxEO2D+yoxCAIMpxThegpsqNH9pqg1CSKDogZHp8SDCg0uZ/EGqQZeJEkI8JR0nYjBRjolMvoDaTpcAFEIYSNmOm9CJfRk3puDTTL6ZaqLbANogiPmUjegSkauxL1GN+biHiX9G7RYH9grCiKYsxni8Eod2UhdRJ1qBG5uwoZM1WID69fkqao/8Ce/EU3dObVaHAAAAAElFTkSuQmCC"  # pylint: disable=line-too-long
DEFAULT_ICON_UNINSTALL = "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"  # pylint: disable=line-too-long


class IconGenerator(DmgMounter):
    """
    Generate icons from an icns file
    """

    description = (
        "Extracts an app icon and saves it to disk. Optionally creates "
        "composite images."
    )
    input_variables = {
        "source_icon": {
            "required": False,
            "description": "The input path of the icon. This can be supplied "
            "as an alternative to the app path",
        },
        "source_app": {
            "required": False,
            "description": "Path to the .app from which to extract an icon. "
            "Can point to a path inside a .dmg which will be mounted. This "
            "path may also contain basic globbing characters such as the "
            "wildcard '*', but only the first result will be returned.",
        },
        "icon_output_path": {
            "required": False,
            "description": "The output path to write the .png icon. If not "
            "set, defaults to %RECIPE_CACHE_DIR%/%NAME%.png",
        },
        "composite_install_path": {
            "required": False,
            "description": "The output path to write the composited 'install' "
            "icon .png, where `composite_install_template` is superimposed on "
            "top of the app icon. If not set, no 'install' composite icon will "
            "be created.",
        },
        "composite_install_template": {
            "required": False,
            "description": "Path to a template icon to composite on top of the "
            "app's icon to create an 'install' icon version. If not set, a "
            "default template icon is used.",
        },
        "composite_update_path": {
            "required": False,
            "description": "The output path to write the composited 'update' "
            "icon .png, where `composite_update_template` is superimposed on "
            "top of the app icon. If not set, no 'update' composite icon will "
            "be created.",
        },
        "composite_update_template": {
            "required": False,
            "description": "Path to a template icon to composite on top of the "
            "app's icon to create an 'update' icon version. If not set, a "
            "default template icon is used.",
        },
        "composite_uninstall_path": {
            "required": False,
            "description": "The output path to write the composited 'uninstall' "
            "icon .png, where `composite_uninstall_template` is superimposed on "
            "top of the app icon. If not set, no 'uninstall' composite icon will "
            "be created.",
        },
        "composite_uninstall_template": {
            "required": False,
            "description": "Path to a template icon to composite on top of the "
            "app's icon to create an 'uninstall' icon version. If not set, a "
            "default template icon is used.",
        },
        "composite_position": {
            "required": False,
            "description": "The anchor position at which to add the composited "
            "template icons. One of: `br` (bottom right), `bl` (bottom left), "
            "`ur` (upper right), or ul (upper left). Defaults to `br`.",
        },
        "composite_padding": {
            "required": False,
            "description": "The number of both horizontal and vertical pixels "
            "to add as padding from the edge of the app icon when compositing "
            "a template icon on top. Defaults to `10`.",
        },
    }
    output_variables = {
        "app_icon_path": {
            "description": "The path on disk to the plain, uncomposited app icon."
        },
        "install_icon_path": {
            "description": "The path on disk to the 'install' composited icon "
            "variation, if requested."
        },
        "update_icon_path": {
            "description": "The path on disk to the 'update' composited icon "
            "variation, if requested."
        },
        "uninstall_icon_path": {
            "description": "The path on disk to the 'uninstall' composited icon "
            "variation, if requested."
        },
    }
    description = __doc__

    def get_path_to_file(self, filename):
        """Find a file in a recipe without requiring a path. Looks in the following places
        in the following order:
        1. RecipeOverrides directory/ies
        2. Same directory as the recipe
        3. Same repo (recipe search directory) as the recipe
        4. Parent recipe's repo (recipe search directory) if recipe is an override
        Relative paths also work."""
        recipe_dir = self.env.get("RECIPE_DIR")
        recipe_dir_path = Path(os.path.expanduser(recipe_dir))
        filepath = os.path.join(recipe_dir, filename)
        matched_override_dir = ""

        # first, look in the overrides directory
        if self.env.get("RECIPE_OVERRIDE_DIRS"):
            matched_filepath = ""
            for d in self.env["RECIPE_OVERRIDE_DIRS"]:
                override_dir_path = Path(os.path.expanduser(d))
                if (
                    override_dir_path == recipe_dir_path
                    or override_dir_path in recipe_dir_path.parents
                ):
                    self.output(f"Matching dir: {override_dir_path}", verbose_level=3)
                    matched_override_dir = override_dir_path
                for path in Path(os.path.expanduser(d)).rglob(filename):
                    matched_filepath = str(path)
                    break
            if matched_filepath:
                self.output(f"File found at: {matched_filepath}")
                return matched_filepath

        # second, look in the same directory as the recipe
        self.output(f"Looking for {filename} in {recipe_dir}", verbose_level=3)
        if os.path.exists(filepath):
            self.output(f"File found at: {filepath}")
            return filepath

        # third, try to match the recipe's dir with one of the recipe search dirs
        if self.env.get("RECIPE_SEARCH_DIRS"):
            matched_filepath = ""
            for d in self.env["RECIPE_SEARCH_DIRS"]:
                search_dir_path = Path(os.path.expanduser(d))
                if (
                    search_dir_path == recipe_dir_path
                    or search_dir_path in recipe_dir_path.parents
                ):
                    # matching search dir, look for file in here
                    self.output(f"Matching dir: {search_dir_path}", verbose_level=3)
                    for path in Path(os.path.expanduser(d)).rglob(filename):
                        matched_filepath = str(path)
                        break
                if matched_filepath:
                    self.output(f"File found at: {matched_filepath}")
                    return matched_filepath

        # fourth, look in the parent recipe's directory if we are an override
        if matched_override_dir:
            if self.env.get("PARENT_RECIPES"):
                matched_filepath = ""
                parent = self.env["PARENT_RECIPES"][0]
                self.output(f"Parent Recipe: {parent}", verbose_level=2)
                parent_dir = os.path.dirname(parent)
                # grab the root of this repo
                parent_dir_path = Path(os.path.expanduser(parent_dir))
                for d in self.env["RECIPE_SEARCH_DIRS"]:
                    search_dir_path = Path(os.path.expanduser(d))
                    if (
                        search_dir_path == parent_dir_path
                        or search_dir_path in parent_dir_path.parents
                    ):
                        # matching parent dir, look for file in here
                        self.output(f"Matching dir: {search_dir_path}", verbose_level=3)
                        for path in Path(os.path.expanduser(d)).rglob(filename):
                            matched_filepath = str(path)
                            break
                    if matched_filepath:
                        self.output(f"File found at: {matched_filepath}")
                        return matched_filepath

    def is_base64(self, s: str) -> bool:
        """Returns boolean whether the passed string is a base64-endcoded value.

        Arguments:
            s: string to check

        Returns:
            boolean if string is base64 encoded
        """
        try:
            # Raise an exception if the passed string cannot be decoded as ascii
            s_bytes = bytes(s, encoding="ascii")
            # Test and return the equality of attempting to re-encode the
            # decoded bytes against the original passed string
            return base64.b64encode(base64.b64decode(s_bytes)) == s_bytes
        except binascii.Error:
            return False

    def get_app_icon_path(self, app_path: str) -> str:
        """Returns the full path to the app icon specified in an app's
        Info.plist file if possible.

        Arguments:
            app_path: path to the .app

        Returns:
            string path to the app icon, or None if unable to find it
        """
        if not os.path.exists(app_path):
            return None
        try:
            with open(os.path.join(app_path, "Contents/Info.plist"), "rb") as app_plist:
                info = plistlib.load(app_plist)
        except plistlib.InvalidFileException:
            return None
        # Read the CFBundleIconFile property, or try using the app's name if
        # that property doesn't exist. This won't catch every case of poor app
        # construction but it will catch some.
        app_name = os.path.basename(app_path)
        icon_filename = info.get("CFBundleIconFile", app_name)
        icon_path = os.path.join(app_path, "Contents/Resources", icon_filename)
        # Add .icns if missing
        if not os.path.splitext(icon_path)[1]:
            icon_path += ".icns"
        if os.path.exists(icon_path):
            return icon_path
        return None

    def save_icon_to_destination(self, input_path: str, output_path: str) -> str:
        """Copies the input icns file path to the output file path as a png.

        Arguments:
            input_path: string path to the icns file
            output_path: string path to the destination

        Returns:
            full path to the output file, or None if the operation failed
        """
        try:
            icon = Image.open(input_path)
            if (128, 128, 2) in icon.info.get("sizes"):
                icon.size = (128, 128, 2)
            elif (256, 256) in icon.info.get("sizes"):
                icon.size = (256, 256)
            else:
                self.output("Resizing icon to 256px.")
                icon = icon.resize((256, 256))
            icon.convert("RGBA")
            icon.load()
            icon.save(output_path, format="png")
            return output_path
        except FileNotFoundError as fnferror:
            raise ProcessorError(
                f"Unable to open the source icon at path {input_path}."
            ) from fnferror
        except PermissionError as perror:
            raise ProcessorError(
                f"Unable to save app icon to {output_path} due to permissions."
            ) from perror
        except IOError as ioerror:
            raise ProcessorError(
                f"Unable to save app icon to path {output_path}."
            ) from ioerror
        except ValueError as verror:
            raise ProcessorError(
                f"Unable to open a 256px representation of the icon at {input_path}."
            ) from verror

    def composite_icon(self, icon_path: str, foreground: str, output_path: str) -> str:
        """Creates a composite icon at `output_path` where `foreground` is
        pasted on top of `icon_path` starting at `position` with `padding`
        pixels of padding.

        If the passed `foreground` string is a path that exists, that path is
        used as the source of the foreground image. Otherwise, the `foreground`
        string is assumed to be a base64-encoded string representing an zimage.

        Arguments:
            icon_path: file path to the app icon
            foreground: file path to, or base64 string representation of, a
                template icon to composite on top of the app icon
            output_path: file path to write composited icon

        Returns:
            path to written output composited icon
        """
        # Retrieve or set defaults for position and padding
        position = self.env.get("composite_position", "br")
        # Reset invalid position input to the default of "br" and output a
        # Processor message
        if position not in ["ul", "ur", "br", "bl"]:
            self.output(
                f"Reset invalid composite_position input '{position}' to the default value 'br'."
            )
            position = "br"
        padding = self.env.get("composite_padding", 10)
        # Reset invalid padding input to the default value '10' and output a
        # Processor message
        if not isinstance(padding, int) and padding >= 0:
            self.output(
                f"Reset invalid composite_padding input '{padding}' to the default value '10'."
            )
            padding = 10

        # If the passed `foreground` doesn't appear to be a local path, but is a
        # base64-encoded string, decode that string so that it can be used by
        # PIL as an image source.
        if not os.path.exists(foreground) and self.is_base64(foreground):
            foreground = io.BytesIO(base64.b64decode(foreground))

        # Open the background image
        bg = Image.open(icon_path)
        # Set the size to the 256px representation (128px square @2x resolution)
        # Note: this is hardcoded as a default for several reasons:
        #   1. This is the default representation size for most first-party
        #      Apple apps.
        #   2. Allowing the recipe to set custom sizes would balloon the number
        #      of input variables to manage.
        #   3. It might be confusing and complicate error handling if a recipe
        #      passed a larger representation that may not be available.
        #   4. PRs accepted for improvements :)
        if (128, 128, 2) in bg.info["sizes"]:
            bg.size = (128, 128, 2)
        elif (256, 256) in bg.info["sizes"]:
            bg.size = (256, 256)
        else:
            self.output("Resizing icon to 256px.")
            bg = bg.resize((256, 256))
        bg.convert("RGBA")
        bg.load()
        # Open the foreground template
        fg = Image.open(foreground).convert("RGBA")

        # Determine the coordinates to anchor the pasted image
        if position == "ul":
            coords = (0 + padding, 0 + padding)
        elif position == "ur":
            coords = (bg.size[0] - (fg.size[0] + padding), 0 + padding)
        elif position == "bl":
            coords = (0 + padding, bg.size[1] - (fg.size[1] + padding))
        # This handles the default case of br (bottom right) or any other
        # invalid input
        else:
            coords = (
                bg.size[0] - (fg.size[0] + padding),
                bg.size[1] - (fg.size[1] + padding),
            )

        # Pastes the foreground onto the background. The third parameter
        # re-specifies the foreground as the paste mask to preserve
        # transparency.
        composite = bg.copy()
        composite.paste(fg, coords, fg)
        try:
            composite.save(output_path, format="png")
        except IOError as ioerror:
            raise ProcessorError(f"Unable to save output to {output_path}") from ioerror

        # Close the images
        bg.close()
        fg.close()

        return output_path

    def main(self):
        """Main"""
        # Retrieve or set a default output path for the app icon
        if self.env.get("icon_output_path"):
            app_icon_output_path = self.env.get("icon_output_path")
        else:
            recipe_dir = self.env["RECIPE_CACHE_DIR"]
            icon_name = self.env["NAME"]
            app_icon_output_path = os.path.join(recipe_dir, icon_name + ".png")

        # get a specified icon path if provided
        source_icon = self.env.get("source_icon")

        # Retrieve the app path
        source_app = self.env.get("source_app")

        if source_icon:
            if source_icon.lower().endswith(".icns") or source_icon.lower().endswith(
                ".png"
            ):
                app_icon_path = self.get_path_to_file(source_icon)
                # icon_path = source_icon
            else:
                # invalid icon provided
                raise ProcessorError("Provided icon is not valid.")
            if not os.path.exists(app_icon_path):
                raise ProcessorError("Could not determine path to provided icon.")
        elif source_app:
            # Determine if the app path is within a dmg
            (dmg_path, dmg, dmg_app_path) = self.parsePathForDMG(source_app)
            if dmg:
                # Mount dmg and return app path inside
                mount_point = self.mount(dmg_path)
                app_path = os.path.join(mount_point, dmg_app_path)
            else:
                # Use the source path as-is, assuming it's a full path to a .app
                app_path = source_app

            # Extract the app icon to the destination path
            app_icon_path = self.get_app_icon_path(app_path)
            if not app_icon_path:
                raise ProcessorError(
                    f"Unable to determine app icon path for app at {app_path}."
                )
        else:
            # no icon provided
            raise ProcessorError("Unable to determine icon path.")

        icon_path = self.save_icon_to_destination(app_icon_path, app_icon_output_path)
        self.env["app_icon_path"] = icon_path

        # Create an 'install' version if requested
        if self.env.get("composite_install_path"):
            install_path = self.env.get("composite_install_path")
            install_template = self.env.get(
                "composite_install_template", DEFAULT_ICON_INSTALL
            )
            install_icon = self.composite_icon(
                app_icon_path, install_template, install_path
            )
            self.env["install_icon_path"] = install_icon

        # Create an 'uninstall' version if requested
        if self.env.get("composite_uninstall_path"):
            uninstall_path = self.env.get("composite_uninstall_path")
            uninstall_template = self.env.get(
                "composite_uninstall_template", DEFAULT_ICON_UNINSTALL
            )
            uninstall_icon = self.composite_icon(
                app_icon_path, uninstall_template, uninstall_path
            )
            self.env["uninstall_icon_path"] = uninstall_icon

        # Create an 'update' version if requested
        if self.env.get("composite_update_path"):
            update_path = self.env.get("composite_update_path")
            update_template = self.env.get(
                "composite_update_template", DEFAULT_ICON_UPDATE
            )
            update_icon = self.composite_icon(
                app_icon_path, update_template, update_path
            )
            self.env["update_icon_path"] = update_icon

        # If we mounted a dmg, unmount it
        if dmg:
            self.unmount(dmg_path)


if __name__ == "__main__":
    processor = IconGenerator()
    processor.execute_shell()
