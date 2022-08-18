#!/usr/local/autopkg/python
#
# Copyright 2020 Graham Pugh
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

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["StringReplacer"]


class StringReplacer(Processor):
    """This processor replaces a string within a variable with another string.
    Example would be to remove a file suffix from a string:
    input_string: "filename.dmg"
    string_to_replace: ".dmg"
    replacement_string: ""
    output_string: "filename"
    """

    input_variables = {
        "input_string": {
            "required": True,
            "description": "The version string that needs splitting.",
        },
        "string_to_replace": {
            "required": False,
            "description": "The character or string to be replaced",
            "default": "",
        },
        "replacement_string": {
            "required": False,
            "description": "The replacement character or string",
            "default": "",
        },
    }
    output_variables = {
        "output_string": {"description": "The string that has been worked on.",}
    }

    description = __doc__

    def main(self):
        """Main process."""
        input_string = self.env.get("input_string")
        string_to_replace = self.env.get("string_to_replace")
        replacement_string = self.env.get("replacement_string")
        self.output("Input String: {}".format(input_string))
        output_string = input_string.replace(string_to_replace, replacement_string)
        self.env["output_string"] = output_string
        self.output("Output String: {}".format(output_string))


if __name__ == "__main__":
    PROCESSOR = StringReplacer()
    PROCESSOR.execute_shell()
