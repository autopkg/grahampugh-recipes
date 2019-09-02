#!/usr/bin/python
#
# Copyright 2017 Graham Pugh
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

from __future__ import absolute_import

import plistlib

from autopkglib import Processor, ProcessorError

__all__ = ["ParallelsDesktopPackager"]

class ParallelsDesktopPackager(Processor):
    description = ("Inserts the license into the deploy.cfg file of the "
                   "Parallels Desktop Autodeploy.pkg")
    input_variables = {
        "CONFIG_FILE_PATH": {
            "required": True,
            "description": ("the path to deploy.cfg")
        },
        "INFO_PLIST_PATH": {
            "required": True,
            "description": ("the path to Info.plist")
        },
        "license_key": {
            "required": True,
            "description": ("the license key")
        },
        "software_updates_check": {
            "required": False,
            "description": ("0 - never",
                            "1 - once a day",
                            "2 - once a week",
                            "3 - once a month"),
            "default": "0"
        },
        "software_updates_auto_download": {
            "required": False,
            "description": ("on or off"),
            "default": "off"
        },
        "version": {
            "required": True,
            "description": "the package version number"
        },
    }
    output_variables = {
    }

    __doc__ = description

    def main(self):
        CONFIG_FILE_PATH = self.env.get("CONFIG_FILE_PATH")
        INFO_PLIST_PATH = self.env.get("INFO_PLIST_PATH")
        license_key = self.env.get("license_key")
        version = self.env.get("version")
        su_check = self.env.get("software_updates_check")
        su_auto_download = self.env.get("software_updates_auto_download")

        # text as will be replaced in deploy.cfg
        license_key_string_before = "license_key=\"XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX\""
        license_key_string_after = "license_key=\"%s\"" % license_key
        su_check_string_before = "#updates_auto_check=\"2\""
        su_check_string_after = "updates_auto_check=\"%s\"" % su_check
        # su_check_string_after = "updates_auto_check=\"0\""
        su_auto_download_before = "#updates_auto_download=\"on\""
        su_auto_download_after = "updates_auto_download=\"%s\"" % su_auto_download
        # su_auto_download_after = "updates_auto_download=\"off\""

        # Read in the deploy.cfg file
        with open(CONFIG_FILE_PATH, 'r') as file:
            filedata = file.read()

        # Replace the target strings
        for r in ((license_key_string_before, license_key_string_after), (su_check_string_before, su_check_string_after), (su_auto_download_before, su_auto_download_after)):
            filedata = filedata.replace(*r)

        # Write the file out again
        with open(CONFIG_FILE_PATH, 'w') as file:
            file.write(filedata)

        # Now to edit the bundle version in Info.plist
        p = plistlib.readPlist(INFO_PLIST_PATH)
        p["CFBundleShortVersionString"] = version
        plistlib.writePlist(p, INFO_PLIST_PATH)


if __name__ == "__main__":
    processor = Policytool()
    processor.execute_shell()
