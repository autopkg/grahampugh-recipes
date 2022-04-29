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
from autopkglib import Processor  # pylint: disable=import-error
from collections import OrderedDict

try:
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
    from ruamel.yaml import dump
    from ruamel.yaml import add_representer


__all__ = ["JamfRecipeMaker"]


class JamfRecipeMaker(Processor):
    """An AutoPkg processor which will create a new recipe containing the package.
    Designed to be run as a post-processor of a .pkg or .jss recipe."""

    input_variables = {
        "RECIPE_CACHE_DIR": {"required": False, "description": ("RECIPE_CACHE_DIR.")},
        "output_file_path": {
            "description": ("Path to output file."),
            "required": False,
            "default": ".",
        },
        "NAME": {"description": ("The NAME key."), "required": False},
        "identifier_prefix": {
            "description": "The identifier prefix.",
            "required": False,
            "default": "com.github.autopkg.grahampugh-recipes",
        },
        "CATEGORY": {
            "description": ("The package category in Jamf Pro."),
            "required": False,
            "default": "Applications",
        },
        "minimum_os_version": {
            "description": (
                "The minimum OS version compatibility of a package, "
                "determined by a PlistReader processor."
            ),
            "required": False,
            "default": None,
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

        output_file_path = self.env.get("output_file_path")

        name = self.env.get("NAME")
        identifier_prefix = self.env.get("identifier_prefix")
        category = self.env.get("CATEGORY")

        parent_recipe = os.path.basename(self.env.get("RECIPE_CACHE_DIR"))
        output_file_name = name.replace(" ", "") + "-pkg-upload.jamf.recipe.yaml"
        output_file = os.path.join(output_file_path, output_file_name)

        data = {
            "Identifier": (
                identifier_prefix + ".jamf." + name.replace(" ", "") + "-pkg-upload"
            ),
            "ParentRecipe": parent_recipe,
            "MinimumVersion": "2.3",
            "Input": {
                "NAME": name,
                "CATEGORY": category,
            },
            "Process": [],
        }
        data["Process"].append(
            {
                "Processor": "com.github.grahampugh.jamf-upload.processors/JamfCategoryUploader",
                "Arguments": {"category_name": "%CATEGORY%"},
            }
        )
        data["Process"].append(
            {
                "Processor": "com.github.grahampugh.jamf-upload.processors/JamfPackageUploader",
                "Arguments": {
                    "pkg_category": "%CATEGORY%",
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
