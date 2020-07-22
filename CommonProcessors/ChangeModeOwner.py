#!/usr/bin/env python

"""
Adapted from com.github.jessepeterson.munki.PortfolioClient10/ModeChanger.py.
"""

from __future__ import absolute_import

import subprocess

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["ChangeModeOwner"]


class ChangeModeOwner(Processor):
    """Changes file or folder modes and/or owner"""

    input_variables = {
        "resource_path": {"required": True, "description": "Pathname of file/folder",},
        "mode": {
            "required": False,
            "description": 'chmod(1) mode string to apply to file/folder, e.g. "o-w", "755"',
            "default": "",
        },
        "owner": {
            "required": False,
            "description": 'chown(1) owner string to apply to file/folder, e.g. "root"',
            "default": "",
        },
        "group": {
            "required": False,
            "description": 'chown(1) group string to apply to file/folder, e.g. "wheel"',
            "default": "",
        },
    }
    output_variables = {}

    def main(self):
        resource_path = self.env.get("resource_path")
        mode = self.env.get("mode")
        owner = self.env.get("owner")
        group = self.env.get("group")

        if mode:
            (output, error) = subprocess.Popen(
                ["/bin/chmod", "-R", mode, resource_path], stdout=subprocess.PIPE
            ).communicate()
            if error is not None:
                raise ProcessorError(
                    f"Error setting mode (chmod -R {mode}) for {resource_path}"
                )

        if owner:
            (output, error) = subprocess.Popen(
                ["/usr/sbin/chown", "-R", owner, resource_path], stdout=subprocess.PIPE
            ).communicate()
            if error is not None:
                raise ProcessorError(
                    f"Error setting user ownership (chown -R {owner}) for {resource_path}"
                )

        if group:
            (output, error) = subprocess.Popen(
                ["/usr/bin/chgrp", "-R", group, resource_path], stdout=subprocess.PIPE
            ).communicate()
            if error is not None:
                raise ProcessorError(
                    f"Error setting group ownership (chgrp -R {group}) for {resource_path}"
                )


if __name__ == "__main__":
    PROCESSOR = ChangeModeOwner()
    PROCESSOR.execute_shell()
