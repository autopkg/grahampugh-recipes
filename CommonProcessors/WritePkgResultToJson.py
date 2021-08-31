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

import os.path
import json

from autopkglib import Processor  # pylint: disable=import-error


__all__ = ["WritePkgResultToJson"]


class WritePkgResultToJson(Processor):
    """An AutoPkg processor which writes useful results of a recipe to a JSON file, which can be
    used to run a different recipe based on those values."""

    input_variables = {
        "RECIPE_CACHE_DIR": {"required": False, "description": ("RECIPE_CACHE_DIR.")},
        "output_file_path": {
            "description": ("Path to output file."),
            "required": False,
        },
        "output_file_name": {
            "description": ("Name of output file."),
            "required": False,
            "default": "latest_version.json",
        },
        "pkg_path": {
            "description": ("The path where the package is stored."),
            "required": False,
        },
        "pkg_name": {"description": ("The name of the package."), "required": False},
        "pkg_uploaded": {
            "description": ("Was a new package uploaded?."),
            "required": False,
            "default": False,
        },
        "pkg_metadata_updated": {
            "description": ("Was the package metadata updated?."),
            "required": False,
            "default": False,
        },
        "version": {
            "description": ("The current package version."),
            "required": False,
        },
        "license_key": {
            "description": ("The outputted value for license_key."),
            "required": False,
            "default": "",
        },
        "PKG_CATEGORY": {
            "description": ("The package category in Jamf Pro."),
            "required": False,
            "default": "",
        },
    }

    output_variables = {
        "version": {"description": ("The current package version.")},
        "license_key": {"description": ("The outputted value for license_key.")},
        "pkg_path": {"description": ("the package path.")},
        "pkg_name": {"description": ("the package name.")},
        "PKG_CATEGORY": {"description": ("The package category.")},
    }

    description = __doc__

    def get_latest_recipe_run_info(self, output_file):
        """get information from the output files of a LastRecipeRunResult processor"""
        try:
            with open(output_file, "r") as fp:
                data = json.load(fp)
        except (IOError, ValueError):
            data = {}
        return data

    def main(self):
        """output the values to a file in the location provided"""

        output_file_path = self.env.get("output_file_path")
        output_file_name = self.env.get("output_file_name")
        pkg_path = self.env.get("pkg_path")
        pkg_name = self.env.get("pkg_name")
        version = self.env.get("version")
        license_key = self.env.get("license_key")
        category = self.env.get("PKG_CATEGORY")
        pkg_uploaded = self.env.get("pkg_uploaded")
        pkg_metadata_updated = self.env.get("pkg_metadata_updated")

        if pkg_path:
            self.output("Package path: {}".format(pkg_path))
        if pkg_name:
            self.output("Package name: {}".format(pkg_name))
        if version:
            self.output("Version: {}".format(version))
        if license_key:
            self.output("License Key: {}".format(license_key))
        if category:
            self.output("Pkg Category: {}".format(category))

        if not output_file_path:
            output_file_path = self.env.get("RECIPE_CACHE_DIR")
        output_file = os.path.join(output_file_path, output_file_name)

        data = self.get_latest_recipe_run_info(output_file)
        data["pkg_path"] = pkg_path
        data["pkg_name"] = pkg_name
        data["version"] = version
        data["license_key"] = license_key
        data["category"] = category
        data["pkg_uploaded"] = pkg_uploaded
        data["pkg_metadata_updated"] = pkg_metadata_updated

        with open(output_file, "w") as outfile:
            json.dump(data, outfile)

        self.output(f"Results written to: {output_file}")


if __name__ == "__main__":
    PROCESSOR = WritePkgResultToJson()
    PROCESSOR.execute_shell()
