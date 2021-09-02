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

try:
    from plistlib import load as plistReader # Python 3
except:
    from plistlib import readPlist as plistReader # Python 2

import re

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
                "Assumes the Recipe ID is in the format of:  "
                "   local.jss.<name>"
            ),
            "required": False
        },
        "recipe_id": {
            "description": (
                "If the recipe name does not match the NAME variable, "
                "this value can be used to override NAME."
            ),
            "required": False
        },
        "cache_dir": {
            "description": "Path to the cache dir.",
            "required": False,
            "default": "~/Library/AutoPkg/Cache"
        },
        "custom_variables": {
            "description": ( "An array of custom input variables that should be "
                "pulled from the latest receipt.  These would generally be unique "
                "to your environment."
            ),
            "required": False,
        }
    }

    output_variables = {
        "version": {
            "description": "The current package version."
        },
        "version_regex": {
            "description": "The current package version regex."
        },
        "CATEGORY": {
            "description": "The package category."
        },
        "SELF_SERVICE_DESCRIPTION": {
            "description": "The self service description."
        },
        "pkg_path": {
            "description": "The package path."
        },
        "license_key": {
            "description": "The license key."
        },
        "SELF_SERVICE_ICON": {
            "description": "The self service icon."
        },
        "package_notes": {
            "description": "The package notes."
        },
        "prod_name": {
            "description": "The prod name of the Policy."
        },
        "PARENT_RECIPES": {
            "description": "The parent recipes, used to locate the self service icon."
        }
    }

    description = __doc__


    def get_recipe_receipts(self, cache_dir, name):
        """Get the receipts for the passed recipe name.

        Args:
            cache_dir (str): Path to the AutoPkg cache directory.
            name (str): Recipe NAME or ID.

        Raises:
            ProcessorError: Unable to locate receipts for the provided recipe.

        Returns:
            list: A list of recipe receipts.
        """

        self.output(
            "Checking for receipts in folder {}/{}".format(cache_dir, name))

        try:
            files = list(iglob("{}/*{}/receipts/*.plist".format(
                cache_dir, name)))
            files.sort(key=lambda x: getmtime(x), reverse=True)
            return files

        except IOError:
            raise ProcessorError("No receipts found!")


    def main(self):
        """Find the latest receipt that contains all 
            the information we're looking for.

        Raises:
            ProcessorError: Proper input variables must be supplied.
            ProcessorError: Package does not exist at the path found.
            ProcessorError: Unable to locate a receipt 
                            with the desired information.
        """

        name = self.env.get("name")
        recipe_id = self.env.get("recipe_id")
        custom_variables = self.env.get("custom_variables", [])
        cache_dir = expanduser(self.env.get("cache_dir", "~/Library/AutoPkg/Cache"))
        version_found = False
        found_parent_recipes = False

        if name:
            name = "local.jss.{}".format(name)

        elif recipe_id:
            name = recipe_id

        else:
            raise ProcessorError("Either 'name' or 'recipe_id' must be provided.")

        receipts = self.get_recipe_receipts(cache_dir, name)

        for receipt in receipts:

            try:
                self.output("Scanning receipt:  {}".format(receipt))

                with open(receipt, 'rb') as plist_receipt:
                    plist = plistReader(plist_receipt)

                if str(plist[-1].keys()) == "dict_keys(['RecipeError'])":
                    self.output("  -> Skipping as this receipt had an error...")
                    continue

                for step in plist:
                    
                    if step.get("Recipe input"):

                        recipe_input = step.get("Recipe input")
                        parent_recipes = recipe_input.get("PARENT_RECIPES")

                        if parent_recipes:
                            found_parent_recipes = True
                            self.env["PARENT_RECIPES"].extend(parent_recipes)
                            self.env["PARENT_RECIPES"].append(recipe_input.get("RECIPE_DIR"))
                            self.env["PARENT_RECIPES"].append(recipe_input.get("RECIPE_PATH"))
                            self.output("Parent Recipes:  {}".format(
                                self.env["PARENT_RECIPES"]), verbose_level=2)

                        for key in custom_variables:
                            self.env[key] = recipe_input.get(key)
                            self.output("{}:  {}".format(key, self.env[key]), verbose_level=2)

                        self.env["NAME"] = recipe_input.get("NAME")
                        self.output("NAME:  {}".format(self.env["NAME"]), verbose_level=2)

                        continue

                    if step.get("Processor"):

                        if step.get("Processor") == "ch.eth.id.check.itshop/ITShopUpdateChecker":
                            license_key = step.get("Output").get("license_key")
                            continue

                        if step.get("Processor") == \
                            "com.github.grahampugh.recipes.commonprocessors/VersionRegexGenerator":
                            version_regex = step.get("Output").get("version_regex")
                            continue

                        if re.search("InputVariableTextSubstituter", step.get("Processor"), re.IGNORECASE):
                            processor_output = step.get("Output")
                            key = processor_output.get("return_variable")
                            value = processor_output.get("return_variable_value")
                            self.output("{}:  {}".format(key, value), verbose_level=2)
                            self.env[key] = value
                            continue

                        if re.search("JSSImporter", step.get("Processor"), re.IGNORECASE):
                            jssimporter_input = step.get("Input")

                            for key, value in jssimporter_input.items():

                                # We don't want to pull these values, incase they're different.
                                if key not in { 
                                    "API_PASSWORD", "API_USERNAME", "JSS_REPOS", "JSS_URL", "JSS_VERIFY_SSL" }:

                                    # Set the proper CASE for these variables
                                    var_name = ( key if key in { "pkg_path", "prod_name", "version" } 
                                        else key.upper() )

                                    self.env[var_name] = value
                                    self.output("{}:  {}".format(var_name, self.env[var_name]), verbose_level=2)

                            if self.env["version"]:
                                version_found = True

                            continue

                if found_parent_recipes and version_found:
                    break

                else:
                    continue

            except:
                self.output("Missing required information...")
                continue

        try:
            self.env["license_key"] = license_key
            self.output("License Key:  {}".format(license_key), verbose_level=2)
        except UnboundLocalError:
            self.env["license_key"] = ""

        try:
            self.env["version_regex"] = version_regex
            self.output("Version Regex:  {}".format(version_regex), verbose_level=2)
        except UnboundLocalError:
            self.output("No version_regex found in receipt - reverting to version", verbose_level=2)
            self.env["version_regex"] = "^{}$".format(self.env["version"])

        if not version_found:
            raise ProcessorError("Unable to locate a receipt with version!")

        # Make sure the package actually exists
        if not exists(self.env["pkg_path"]):
            raise ProcessorError("Package does not exist:  {}".format(self.env["pkg_path"]))


if __name__ == "__main__":
    PROCESSOR = JSSRecipeReceiptChecker()
    PROCESSOR.execute_shell()
