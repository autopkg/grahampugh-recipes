#!/usr/bin/python
#
# Copyright 2019 Graham Pugh
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
"""See docstring for SubDirectoryList class"""


from __future__ import absolute_import

from builtins import str
import subprocess

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error
from plistlib import writePlist

try:
    from plistlib import readPlistFromString
except ImportError:
    from plistlib import readPlistFromBytes as readPlistFromString

__all__ = ["ChoicesXMLGenerator"]


class ChoicesXMLGenerator(Processor):
    """Generates a choices.xml file for use with an installer. A
    postinstall script is required to run the installer with the
    choices.xml"""

    input_variables = {
        "choices_pkg_path": {
            "description": "Path to start looking for files.",
            "required": True,
        },
        "desired_choices": {
            "description": ("A dictionary of choices." "Defaults to empty"),
            "default": "choice_vpn",
            "required": False,
        },
        "choices_xml_dest": {
            "description": "Path to save the choices.xml file.",
            "required": False,
        },
    }
    output_variables = {}

    description = __doc__

    def output_showchoicesxml(self, choices_pkg_path):
        """Invoke the installer showChoicesXML command and return
        the contents"""
        (choices_plist, error) = subprocess.Popen(
            ["/usr/sbin/installer", "-showChoicesXML", "-pkg", choices_pkg_path],
            stdout=subprocess.PIPE,
        ).communicate()
        if choices_plist:
            try:
                choices_list = readPlistFromString(choices_plist)
            except Exception as err:
                raise ProcessorError(
                    f"Unexpected error parsing manifest as a plist: '{err}'"
                )
            child_items = choices_list[0]["childItems"]
            return child_items
        if error:
            raise ProcessorError("No Plist generated from installer command")

    def parse_choices_list(self, child_items, desired_choices):
        """Generates the python dictionary of choices.
        Desired choices are given the choice attribute '1' (chosen).
        Other choices found are given the choice attribute '0'
        (not chosen). """
        parsed_choices = []
        for child_dict in child_items:
            try:
                choice_identifier = child_dict["choiceIdentifier"]
                if choice_identifier in desired_choices:
                    self.output(f"Selected choice: {str(choice_identifier)}")
                    parsed_choices.append(
                        {
                            "choiceIdentifier": str(choice_identifier),
                            "choiceAttribute": "selected",
                            "attributeSetting": 1,
                        }
                    )
                else:
                    self.output(f"Deselected choice: {str(choice_identifier)}")
                    parsed_choices.append(
                        {
                            "choiceIdentifier": str(choice_identifier),
                            "choiceAttribute": "selected",
                            "attributeSetting": 0,
                        }
                    )
            except:
                pass
        return parsed_choices

    def write_choices_xml(self, parsed_choices, choices_xml_dest):
        """Write the plist to a file"""
        try:
            writePlist(parsed_choices, choices_xml_dest)
        except:
            self.output("Could not write to file")

    def main(self):
        """Do the work."""
        choices_pkg_path = self.env.get("choices_pkg_path")
        desired_choices = self.env.get("desired_choices")
        choices_xml_dest = self.env.get("choices_xml_dest")

        if not choices_pkg_path:
            self.output("No package selected!")
        if not desired_choices:
            self.output("No choices means an empty package!")

        child_items = self.output_showchoicesxml(choices_pkg_path)
        parsed_choices = self.parse_choices_list(child_items, desired_choices)
        self.write_choices_xml(parsed_choices, choices_xml_dest)


if __name__ == "__main__":
    PROCESSOR = ChoicesXMLGenerator()
    PROCESSOR.execute_shell()
