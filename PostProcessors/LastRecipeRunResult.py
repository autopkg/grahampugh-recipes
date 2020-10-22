#!/usr/bin/python
#
# 2019 Graham R Pugh
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
"""See docstring for LastRecipeRunResult class"""

import plistlib
import os.path
import sys
import json

from distutils.version import LooseVersion
from os.path import expanduser, getmtime, exists
from autopkglib import Processor, ProcessorError  # pylint: disable=import-error
from glob import iglob


__all__ = ["LastRecipeRunResult"]


class LastRecipeRunResult(Processor):
    """An AutoPkg processor which writes useful results of a recipe to a JSON file, which can be used to run a different recipe based on those values."""

    input_variables = {
        "RECIPE_CACHE_DIR": {"required": False, "description": ("RECIPE_CACHE_DIR."),},
        "output_file_path": {
            "description": ("Path to output file."),
            "required": False,
        },
        "output_file_name": {
            "description": ("Name of output file."),
            "required": False,
            "default": "latest_version.json",
        },
        "url": {"description": ("the download URL."), "required": False,},
        "pkg_path": {
            "description": ("The path where the package is stored."),
            "required": False,
        },
        "pathname": {
            "description": ("The path to the downloaded installer."),
            "required": False,
        },
        "version": {
            "description": ("The current package version."),
            "required": False,
        },
        "PKG_CATEGORY": {
            "description": ("The package category in Jamf Pro."),
            "required": False,
        },
        "SELFSERVICE_DESCRIPTION": {
            "description": ("The self-service description in Jamf Pro."),
            "required": False,
        },
    }

    output_variables = {
        "url": {"description": ("the download URL."),},
        "version": {"description": ("The current package version."),},
        "pkg_path": {"description": ("the package path."),},
        "pkg_name": {"description": ("the package name."),},
        "PKG_CATEGORY": {"description": ("The package category."),},
        "SELFSERVICE_DESCRIPTION": {"description": ("The self-service description."),},
    }

    description = __doc__

    def main(self):
        """output the values to a file in the location provided"""

        output_file_path = self.env.get("output_file_path")
        output_file_name = self.env.get("output_file_name")
        pathname = self.env.get("pathname")
        pkg_path = self.env.get("pkg_path")
        pkg_name = self.env.get("pkg_name")
        url = self.env.get("url")
        version = self.env.get("version")
        category = self.env.get("PKG_CATEGORY")
        self_service_description = self.env.get("SELFSERVICE_DESCRIPTION")

        self.output("Download: {}".format(pathname))
        self.output("Package path: {}".format(pkg_path))
        self.output("Package name: {}".format(pkg_name))
        self.output("URL: {}".format(url))
        self.output("Version: {}".format(version))
        self.output("Pkg Category: {}".format(category))
        self.output("Self Service Description: {}".format(self_service_description))

        data = {}
        data["pathname"] = pathname
        data["pkg_path"] = pkg_path
        data["pkg_name"] = pkg_name
        data["url"] = url
        data["version"] = version
        data["category"] = category
        data["self_service_description"] = self_service_description

        if not output_file_path:
            output_file_path = self.env.get("RECIPE_CACHE_DIR")

        with open(os.path.join(output_file_path, output_file_name), "w") as outfile:
            json.dump(data, outfile)

        self.output(
            f"Results written to: {os.path.join(output_file_path, output_file_name)}"
        )


if __name__ == "__main__":
    PROCESSOR = LastRecipeRunResult()
    PROCESSOR.execute_shell()
