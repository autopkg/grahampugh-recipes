#!/usr/local/autopkg/python
# pylint: disable=invalid-name

"""
Copyright 2026 Graham Pugh

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

NOTES:
This processor creates a plist file from a dictionary input.
The input can be from a YAML or PLIST formatted AutoPkg recipe.
"""

import os
import plistlib

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error


__all__ = ["CreatePlist"]


class CreatePlist(Processor):
    """A processor for AutoPkg that creates a plist file from a dictionary input.

    The plist_content input can contain simple key-value pairs, nested dictionaries,
    or arrays. This works seamlessly whether the recipe is in YAML or PLIST format,
    as AutoPkg handles the conversion to Python dictionaries before the processor runs.
    """

    description = (
        "Creates a plist file from a dictionary input. The plist_content input "
        "can contain simple key-value pairs, nested dictionaries, or arrays. "
        "The file is written to RECIPE_CACHE_DIR by default."
    )

    input_variables = {
        "output_file_name": {
            "required": True,
            "description": (
                "Name of the output plist file. If it does not end with '.plist', "
                "the extension will be appended."
            ),
        },
        "plist_content": {
            "required": True,
            "description": (
                "Dictionary containing the content to write to the plist file. "
                "Can contain simple key-value pairs, nested dictionaries, or arrays. "
                "This input works with both YAML and PLIST formatted recipes."
            ),
        },
        "output_dir": {
            "required": False,
            "description": (
                "Directory to save the plist file. Defaults to RECIPE_CACHE_DIR."
            ),
        },
    }

    output_variables = {
        "plist_path": {
            "description": "Full path to the created plist file.",
        },
        "createplist_summary_result": {
            "description": "Description of interesting results.",
        },
    }

    def main(self):
        """Main process to create the plist file."""
        output_file_name = self.env.get("output_file_name")
        plist_content = self.env.get("plist_content")
        output_dir = self.env.get("output_dir") or self.env.get("RECIPE_CACHE_DIR")

        # Validate inputs
        if not output_file_name:
            raise ProcessorError("output_file_name is required")
        if plist_content is None:
            raise ProcessorError("plist_content is required")
        if not isinstance(plist_content, dict):
            raise ProcessorError(
                f"plist_content must be a dictionary, got {type(plist_content).__name__}"
            )

        # Ensure the output file has a .plist or .mobileconfig extension
        if not (
            output_file_name.endswith(".plist")
            or output_file_name.endswith(".mobileconfig")
        ):
            output_file_name = f"{output_file_name}.plist"

        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.output(f"Created output directory: {output_dir}")
            except OSError as e:
                raise ProcessorError(
                    f"Could not create output directory {output_dir}: {e}"
                ) from e

        # Construct the full output path
        plist_path = os.path.join(output_dir, output_file_name)

        # Write the plist file
        try:
            with open(plist_path, "wb") as plist_file:
                plistlib.dump(plist_content, plist_file)
            self.output(f"Created plist file: {plist_path}")
        except Exception as e:
            raise ProcessorError(f"Could not write plist file: {e}") from e

        # Set output variables
        self.env["plist_path"] = plist_path
        self.env["createplist_summary_result"] = {
            "summary_text": "The following plist file was created:",
            "report_fields": ["plist_path"],
            "data": {"plist_path": plist_path},
        }


if __name__ == "__main__":
    PROCESSOR = CreatePlist()
    PROCESSOR.execute_shell()
