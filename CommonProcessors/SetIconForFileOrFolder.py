#!/usr/bin/python
#
# 2018 Graham R Pugh
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

import Cocoa
import sys
import os
from autopkglib import Processor, ProcessorError

__all__ = ["SetIconForFileOrFolder"]

class SetIconForFileOrFolder(Processor):
    '''Takes an icns file and associates it with a file or folder'''
    input_variables = {
        "icns_filepath": {
            "required": True,
            "description": ("Path to icns file"),
        },
        "icns_destination": {
            "required": True,
            "description": ("Path to file or folder to place icon"),
        },
    }

    output_variables = {}

    description = __doc__

    def writeIcon(self, input, dest):
        '''Copy the icon and do the necessary stuff'''
        try:
            Cocoa.NSWorkspace.sharedWorkspace().setIcon_forFile_options_(Cocoa.NSImage.alloc().initWithContentsOfFile_(input.decode('utf-8')), dest.decode('utf-8'), 0)
        except RuntimeError:
            sys.exit("Unable to set file icon")

    def main(self):
            # import variables from recipe
            icns_filepath = self.env.get('icns_filepath')
            icns_destination = self.env.get('icns_destination')

if __name__ == '__main__':
    PROCESSOR = SetIconForFileOrFolder()
    PROCESSOR.execute_shell()
