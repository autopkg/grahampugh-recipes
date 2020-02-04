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

import subprocess

from autopkglib import Processor, ProcessorError
from FoundationPlist import readPlistFromString, writePlist

__all__ = ["ChoicesXMLGenerator"]


class ChoicesXMLGenerator(Processor):
    """Generates a choices.xml file for use with an installer. A postinstall script is required to run the installer with the choices.xml"""
    input_variables = {
        'choices_pkg_path': {
            'description': 'Path to start looking for files.',
            'required': True,
        },
        'desired_choices': {
            'description': ("A dictionary of choices."
                            "Defaults to empty"),
            'default': 'choice_vpn',
            'required': False,
        },
        'choices_xml_dest': {
            'description': 'Path to save the choices.xml file.',
            'required': False,
        },
    }
    output_variables = {
    }

    description = __doc__


    def output_showchoicesxml(self, choices_pkg_path):
        '''Invoke the installer showChoicesXML command and return the contents'''
        (choices_plist, error) = subprocess.Popen(['/usr/sbin/installer', '-showChoicesXML', '-pkg', choices_pkg_path], stdout=subprocess.PIPE).communicate()
        if choices_plist:
            try:
                choices_list = readPlistFromString(choices_plist)
                return choices_list
            except:
                self.output('Could not read Plist.')
        if error:
            self.output('No Plist generated from installer command')


    def parse_choices_list(self, choices_list, desired_choices):
        '''Generates the python dictionary of choices.
        Desired choices are given the choice attribute '1' (chosen).
        Other choices found are given the choice attribute '0' (not chosen). '''
        parsed_choices = []
        # read the showChoicesXML output file
        for item_dict in choices_list.itervalues():
            try:
                child_items = item_dict['childItems']
            except:
                self.output('Plist has no child items.')
        for child_dict in child_items:
            try:
                choice_identifier = child_dict['choiceIdentifier']
                if choice_identifier in desired_choices:
                    parsed_choices.append({'choiceIdentifier': str(choice_identifier), 'choiceAttribute': 'selected', 'attributeSetting':1})
                else:
                    parsed_choices.append({'choiceIdentifier': str(choice_identifier), 'choiceAttribute': 'selected', 'attributeSetting':0})
            except:
                pass
        return parsed_choices


    def write_choices_xml(self, parsed_choices, choices_xml_dest):
        '''Write the plist to a file'''
        try:
            writePlist(parsed_choices, choices_xml_dest)
        except:
            self.output('Could not write to file')


    def main(self):
        '''Do the work.'''
        choices_pkg_path = self.env.get('choices_pkg_path')
        desired_choices = self.env.get('desired_choices')
        choices_xml_dest = self.env.get('choices_xml_dest')

        if not choices_pkg_path:
            self.output('No package selected!')
        if not desired_choices:
            self.output('No choices means an empty package!')


        choices_list = self.output_showchoicesxml(choices_pkg_path)
        parsed_choices = self.parse_choices_list(choices_list, desired_choices)
        self.write_choices_xml(parsed_choices, choices_xml_dest)


if __name__ == '__main__':
    PROCESSOR = ChoicesXMLGenerator()
    PROCESSOR.execute_shell()
