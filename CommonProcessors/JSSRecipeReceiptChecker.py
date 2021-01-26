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
"""See docstring for JSSRecipeReceiptChecker class"""

from __future__ import absolute_import
import plistlib

from glob import iglob
from os.path import expanduser, getmtime, exists
from autopkglib import Processor, ProcessorError  # pylint: disable=import-error


__all__ = ["JSSRecipeReceiptChecker"]


class JSSRecipeReceiptChecker(Processor):
    """An AutoPkg processor which works out the latest receipt from a different
    AutoPkg recipe, and provides useful values from its contents, which can be
    used to run a different recipe based on those values."""

    input_variables = {
        "name": {
            "description": (
                "This value should be the same as the NAME in the recipe "
                "from which we want to read the receipt. This is all we "
                "need to construct the override path."
            ),
            "required": True,
        },
        "RECIPE_NAME": {
            "description": (
                "If the recipe name does not match the NAME variable, "
                "this value can be used to override NAME."
            ),
            "required": False,
        },
        "cache_dir": {
            "description": "Path to the cache dir.",
            "required": False,
            "default": "~/Library/AutoPkg/Cache",
        },
    }

    output_variables = {
        "version": {"description": "The current package version."},
        "version_regex": {"description": "The current package version regex."},
        "CATEGORY": {"description": "The package category."},
        "SELF_SERVICE_DESCRIPTION": {"description": "The self-service description."},
        "pkg_path": {"description": "the package path."},
        "license_key": {"description": "the license key."},
    }

    description = __doc__

    def get_latest_receipt(self, cache_dir, name, receipt_number):
        """name of receipt with the highest version number"""
        self.output(
            "Checking for receipts in folder {}/local.jss.{}".format(cache_dir, name)
        )
        files = list(iglob("{}/local.jss.{}/receipts/*.plist".format(cache_dir, name)))
        files.sort(key=lambda x: getmtime(x), reverse=True)
        return files[receipt_number]

    def main(self):
        """do the main thing"""
        name = self.env.get("name")
        recipe_name = self.env.get("RECIPE_NAME")
        cache_dir = expanduser(self.env.get("cache_dir"))
        version_found = False

        if recipe_name:
            name = recipe_name

        receipt_number = 0
        while not version_found:
            try:
                receipt = self.get_latest_receipt(cache_dir, name, receipt_number)
            except IOError:
                raise ProcessorError("No receipt found!")

            self.output("Receipt: {}".format(receipt))

            plist = plistlib.readPlist(receipt)
            i = 0
            while i < len(plist):
                try:
                    processor = plist[i]["Processor"]
                    if processor == "ch.ethz.id.check.itshop/ITShopUpdateChecker":
                        license_key = plist[i]["Output"]["license_key"]
                    if (
                        processor
                        == "com.github.grahampugh.recipes.commonprocessors/VersionRegexGenerator"
                    ):
                        version_regex = plist[i]["Output"]["version_regex"]
                    if processor == "JSSImporter":
                        version = plist[i]["Input"]["version"]
                        if plist[i]["Input"]["pkg_path"] != "":
                            pkg_path = plist[i]["Input"]["pkg_path"]
                        category = plist[i]["Input"]["category"]
                        self_service_description = plist[i]["Input"][
                            "self_service_description"
                        ]
                        version_found = True
                        break
                except KeyError:
                    self.output("No JSSImporter process in: {}".format(receipt))
                i = i + 1

            # make sure all the values were obtained from the receipt
            try:
                self.env["version"] = version
                self.output("Version: {}".format(version))
                if pkg_path:
                    self.env["pkg_path"] = pkg_path
                else:
                    self.env["pkg_path"] = ""
                self.output("Package: {}".format(pkg_path))
                self.env["CATEGORY"] = category
                self.output("Category: {}".format(category))
                self.env["SELF_SERVICE_DESCRIPTION"] = self_service_description
                self.output(
                    "Self Service Description: {}".format(self_service_description)
                )
                try:
                    self.env["license_key"] = license_key
                    self.output("License Key: {}".format(license_key))
                except UnboundLocalError:
                    self.env["license_key"] = ""
                try:
                    self.env["version_regex"] = version_regex
                    self.output("Version Regex: {}".format(version_regex))
                except UnboundLocalError:
                    self.output(
                        "No version_regex found in receipt - reverting to version"
                    )
                    self.env["version_regex"] = "^{}$".format(version)
            except UnboundLocalError:
                self.output("No version found in receipt")
                receipt_number = receipt_number + 1

        # make sure the package actually exists
        if not exists(pkg_path):
            raise ProcessorError("Package does not exist: {}".format(pkg_path))
        # end


if __name__ == "__main__":
    PROCESSOR = JSSRecipeReceiptChecker()
    PROCESSOR.execute_shell()
