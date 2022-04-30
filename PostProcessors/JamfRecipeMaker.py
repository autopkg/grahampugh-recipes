#!/usr/bin/python
#
# 2022 Graham R Pugh
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
import subprocess
import sys
from collections import OrderedDict
from plistlib import load as load_plist
from autopkglib import Processor  # pylint: disable=import-error

try:
    from ruamel import yaml
    from ruamel.yaml import dump
    from ruamel.yaml import add_representer
    from ruamel.yaml.nodes import MappingNode
except ImportError:
    subprocess.check_call([sys.executable, "-m", "ensurepip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip3",
            "install",
            "-U",
            "pip",
            "setuptools",
            "wheel",
            "ruamel.yaml",
            "--user",
        ]
    )
    from ruamel import yaml
    from ruamel.yaml import dump
    from ruamel.yaml import add_representer
    from ruamel.yaml.nodes import MappingNode


__all__ = ["JamfRecipeMaker"]


class JamfRecipeMaker(Processor):
    """An AutoPkg processor which will create a new recipe containing the package.
    Designed to be run as a post-processor of a .pkg or .jss recipe."""

    input_variables = {
        "RECIPE_CACHE_DIR": {"required": False, "description": ("RECIPE_CACHE_DIR.")},
        "RECIPE_OUTPUT_PATH": {
            "description": ("Path to output file."),
            "required": False,
            "default": ".",
        },
        "NAME": {"description": ("The NAME key."), "required": False},
        "POLICY_NAME": {
            "description": ("The desired policy name."),
            "required": False,
            "default": "Install Latest %NAME%",
        },
        "POLICY_TEMPLATE": {
            "description": ("The desired policy template."),
            "required": False,
            "default": "JamfPolicyTemplate.xml",
        },
        "GROUP_NAME": {
            "description": ("The desired smart group name."),
            "required": False,
            "default": "%NAME%-update-smart",
        },
        "GROUP_TEMPLATE": {
            "description": ("The desired smart group template."),
            "required": False,
            "default": "JamfSmartGroupTemplate.xml",
        },
        "RECIPE_IDENTIFIER_PREFIX": {
            "description": "The identifier prefix.",
            "required": False,
            "default": "com.github.autopkg.grahampugh-recipes",
        },
        "CATEGORY": {
            "description": ("The package category in Jamf Pro."),
            "required": False,
            "default": "Applications",
        },
        "SELF_SERVICE_DESCRIPTION": {
            "description": (
                "The Self Service Description in Jamf Pro - requires running against a jss recipe."
            ),
            "required": False,
            "default": "",
        },
        "make_categories": {
            "description": ("Add JamfCategoryUploader process if true."),
            "required": False,
            "default": False,
        },
        "add_regex": {
            "description": ("Add VersionRegexGenerator process if true."),
            "required": False,
            "default": False,
        },
        "make_policy": {
            "description": (
                "Add StopProcessingIf, JamfComputerGroupUploader, and "
                "JamfPolicyUploader processes if true."
            ),
            "required": False,
            "default": False,
        },
    }

    output_variables = {
        "CATEGORY": {"description": ("The package category.")},
        "NAME": {"description": ("The NAME.")},
    }

    description = __doc__

    def represent_ordereddict(self, dumper, data):
        value = []

        for item_key, item_value in data.items():
            node_key = dumper.represent_data(item_key)
            node_value = dumper.represent_data(item_value)

            value.append((node_key, node_value))

        return MappingNode("tag:yaml.org,2002:map", value)

    def convert(self, data):
        """Do the conversion."""
        add_representer(OrderedDict, self.represent_ordereddict)
        return dump(data, width=float("inf"), default_flow_style=False)

    def optimise_autopkg_recipes(self, recipe):
        """If input is an AutoPkg recipe, optimise the yaml output in 3 ways to aid
        human readability:

        1. Adjust the Processor dictionaries such that the Comment and Arguments keys are
        moved to the end, ensuring the Processor key is first.
        2. Ensure the NAME key is the first item in the Input dictionary.
        3. Order the items such that the Input and Process dictionaries are at the end.
        """

        if "Process" in recipe:
            process = recipe["Process"]
            new_process = []
            for processor in process:
                processor = OrderedDict(processor)
                if "Comment" in processor:
                    processor.move_to_end("Comment")
                if "Arguments" in processor:
                    processor.move_to_end("Arguments")
                new_process.append(processor)
            recipe["Process"] = new_process

        if "Input" in recipe:
            input = recipe["Input"]
            if "NAME" in input:
                input = OrderedDict(reversed(list(input.items())))
                input.move_to_end("NAME")
            recipe["Input"] = OrderedDict(reversed(list(input.items())))

        desired_order = [
            "Comment",
            "Description",
            "Identifier",
            "ParentRecipe",
            "MinimumVersion",
            "Input",
            "Process",
            "ParentRecipeTrustInfo",
        ]
        desired_list = [k for k in desired_order if k in recipe]
        reordered_recipe = {k: recipe[k] for k in desired_list}
        reordered_recipe = OrderedDict(reordered_recipe)
        return reordered_recipe

    def format_autopkg_recipes(self, output):
        """Add lines between Input and Process, and between multiple processes.
        This aids readability of yaml recipes"""
        # add line before specific processors
        for item in ["Input:", "Process:", "- Processor:", "ParentRecipeTrustInfo:"]:
            output = output.replace(item, "\n" + item)

        # remove line before first process
        output = output.replace("Process:\n\n-", "Process:\n-")

        recipe = []
        lines = output.splitlines()
        for line in lines:
            # convert quoted strings with newlines in them to scalars
            if "\\n" in line:
                spaces = len(line) - len(line.lstrip()) + 2
                space = " "
                line = line.replace(': "', ": |\n{}".format(space * spaces))
                line = line.replace("\\t", "    ")
                line = line.replace('\\n"', "")
                line = line.replace("\\n", "\n{}".format(space * spaces))
                line = line.replace('\\"', '"')
                if line[-1] == '"':
                    line[:-1]
            # elif "%" in lines:
            # handle strings that have AutoPkg %percent% variables in them
            # (these need to be quoted)

            recipe.append(line)
        recipe.append("")
        return "\n".join(recipe)

    def main(self):
        """output the values to a file in the location provided"""

        # set variables
        output_file_path = self.env.get("RECIPE_OUTPUT_PATH")
        name = self.env.get("NAME")
        identifier_prefix = self.env.get("RECIPE_IDENTIFIER_PREFIX")
        category = self.env.get("CATEGORY")
        self_service_description = self.env.get("SELF_SERVICE_DESCRIPTION")
        group_name = self.env.get("GROUP_NAME")
        group_template = self.env.get("GROUP_TEMPLATE")
        policy_name = self.env.get("POLICY_NAME")
        policy_template = self.env.get("POLICY_TEMPLATE")
        make_category = self.env.get("make_category")
        # handle setting make_category in overrides
        if not make_category or make_category == "False":
            make_category = False
        make_policy = self.env.get("make_policy")
        # handle setting make_policy in overrides
        if not make_policy or make_policy == "False":
            make_policy = False
        add_regex = self.env.get("add_regex")
        # handle setting add_regex in overrides
        if not add_regex or add_regex == "False":
            add_regex = False

        # parent recipes dependent on whether we are running a pkg or jss recipe
        parent_recipe = ""
        if ".jss." in self.env.get("RECIPE_CACHE_DIR"):
            for recipe in self.env.get("PARENT_RECIPES"):
                if ".pkg" in recipe and "local." not in recipe:
                    # is the parent recipe a yaml or plist recipe?
                    try:
                        with open(recipe, "rb") as in_file:
                            try:
                                # try to open a yaml recipe
                                parent_recipe_data = yaml.safe_load(in_file)
                                parent_recipe = os.path.basename(
                                    parent_recipe_data["Identifier"]
                                )
                            except yaml.scanner.ScannerError:
                                # try to open a plist recipe
                                parent_recipe_data = load_plist(in_file)
                                parent_recipe = os.path.basename(
                                    parent_recipe_data["Identifier"]
                                )
                    except IOError:
                        self.output(
                            (
                                "WARNING: could not find parent recipe identifier. "
                                f'Defaulting to {self.env.get("RECIPE_CACHE_DIR")} '
                                "which may need editing."
                            )
                        )
                    parent_recipe = os.path.basename(self.env.get("RECIPE_CACHE_DIR"))
            if not parent_recipe:
                self.output(
                    (
                        "WARNING: could not find parent recipe identifier. "
                        f'Defaulting to {self.env.get("RECIPE_CACHE_DIR")} '
                        "which may need editing."
                    )
                )
                parent_recipe = os.path.basename(self.env.get("RECIPE_CACHE_DIR"))
        else:
            parent_recipe = os.path.basename(self.env.get("RECIPE_CACHE_DIR"))

        # filename dependent on whether making policy or not
        if make_policy:
            output_file_name = name.replace(" ", "") + ".jamf.recipe.yaml"
        else:
            output_file_name = name.replace(" ", "") + "-pkg-upload.jamf.recipe.yaml"
        output_file = os.path.join(output_file_path, output_file_name)

        # write recipe data
        # common settings
        data = {
            "Identifier": (
                identifier_prefix + ".jamf." + name.replace(" ", "") + "-pkg-upload"
            ),
            "ParentRecipe": parent_recipe,
            "MinimumVersion": "2.3",
            "Input": {"NAME": name, "CATEGORY": category},
            "Process": [],
        }
        if make_policy:
            data["Identifier"] = identifier_prefix + ".jamf." + name.replace(" ", "")
        else:
            data["Identifier"] = (
                identifier_prefix + ".jamf." + name.replace(" ", "") + "-pkg-upload"
            )

        # JamfCategoryUploader
        if make_category:
            data["Process"].append(
                {
                    "Processor": (
                        "com.github.grahampugh.jamf-upload.processors/JamfCategoryUploader"
                    ),
                    "Arguments": {"category_name": "%CATEGORY%"},
                }
            )
        # JamfPackageUploader
        data["Process"].append(
            {
                "Processor": "com.github.grahampugh.jamf-upload.processors/JamfPackageUploader",
                "Arguments": {"pkg_category": "%CATEGORY%"},
            }
        )
        if make_policy:
            # JamfComputerGroupUploader
            data["Input"]["GROUP_NAME"] = group_name
            data["Input"]["GROUP_TEMPLATE"] = group_template
            data["Input"]["TESTING_GROUP_NAME"] = "Testing"
            data["Input"]["POLICY_CATEGORY"] = "Testing"
            data["Input"]["POLICY_NAME"] = policy_name
            data["Input"]["POLICY_TEMPLATE"] = policy_template
            data["Input"]["SELF_SERVICE_DISPLAY_NAME"] = policy_name
            data["Input"]["SELF_SERVICE_DESCRIPTION"] = self_service_description
            data["Input"]["SELF_SERVICE_ICON"] = "%NAME%.png"
            data["Input"]["UPDATE_PREDICATE"] = "pkg_uploaded == False"
            data["Process"].append(
                {
                    "Processor": "StopProcessingIf",
                    "Arguments": {"predicate": "%UPDATE_PREDICATE%"},
                }
            )
            if add_regex:
                data["Process"].append(
                    {
                        "Processor": (
                            "com.github.grahampugh.recipes.commonprocessors/VersionRegexGenerator"
                        ),
                    }
                )
            data["Process"].append(
                {
                    "Processor": (
                        "com.github.grahampugh.jamf-upload.processors/JamfComputerGroupUploader"
                    ),
                    "Arguments": {
                        "computergroup_name": "%GROUP_NAME%",
                        "computergroup_template": "%GROUP_TEMPLATE%",
                    },
                }
            )
            if make_category:
                data["Process"].append(
                    {
                        "Processor": (
                            "com.github.grahampugh.jamf-upload.processors/JamfCategoryUploader"
                        ),
                        "Arguments": {"category_name": "%POLICY_CATEGORY%"},
                    }
                )
            data["Process"].append(
                {
                    "Processor": (
                        "com.github.grahampugh.jamf-upload.processors/JamfPolicyUploader"
                    ),
                    "Arguments": {
                        "policy_name": "%POLICY_NAME%",
                        "policy_template": "%POLICY_TEMPLATE%",
                    },
                }
            )

        normalized = self.optimise_autopkg_recipes(data)
        output = self.convert(normalized)
        output = self.format_autopkg_recipes(output)

        out_file = open(output_file, "w")
        out_file.writelines(output)
        self.output("Wrote to : {}\n".format(output_file))


if __name__ == "__main__":
    PROCESSOR = JamfRecipeMaker()
    PROCESSOR.execute_shell()
