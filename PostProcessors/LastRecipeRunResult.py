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
from autopkglib import Processor, ProcessorError
from glob import iglob


__all__ = ["LastRecipeRunResult"]


class LastRecipeRunResult(Processor):
    """An AutoPkg processor which works out the latest receipt from a different AutoPkg recipe, and provides useful values from its contents, which can be used to run a different recipe based on those values."""

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
        "pkg_path": {"description": ("the package path."), "required": False,},
        "version": {
            "description": ("The current package version."),
            "required": False,
        },
        "CATEGORY": {"description": ("The package category."), "required": False,},
        "SELF_SERVICE_DESCRIPTION": {
            "description": ("The self-service description."),
            "required": False,
        },
        "url": {"description": ("the download URL."), "required": False,},
    }

    output_variables = {
        "version": {"description": ("The current package version."),},
        "CATEGORY": {"description": ("The package category."),},
        "SELF_SERVICE_DESCRIPTION": {"description": ("The self-service description."),},
        "pkg_path": {"description": ("the package path."),},
        "url": {"description": ("the download URL."),},
    }

    description = __doc__

    def main(self):
        """output the values to a file in the location provided"""

        output_file_path = self.env.get("output_file_path")
        output_file_name = self.env.get("output_file_name")
        pkg_path = self.env.get("pkg_path")
        url = self.env.get("url")
        version = self.env.get("version")
        category = self.env.get("CATEGORY")
        self_service_description = self.env.get("SELF_SERVICE_DESCRIPTION")

        self.output("Package: {}".format(pkg_path))
        self.output("URL: {}".format(url))
        self.output("Version: {}".format(version))
        self.output("Category: {}".format(category))
        self.output("Self Service Description: {}".format(self_service_description))

        data = {}
        data["pkg_path"] = pkg_path
        data["url"] = url
        data["version"] = version
        data["category"] = category
        data["self_service_description"] = self_service_description

        if not output_file_path:
            output_file_path = self.env.get("RECIPE_CACHE_DIR")

        with open(os.path.join(output_file_path, output_file_name), "w") as outfile:
            json.dump(data, outfile)


if __name__ == "__main__":
    PROCESSOR = LastRecipeRunResult()
    PROCESSOR.execute_shell()
