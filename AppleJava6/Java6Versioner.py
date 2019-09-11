#!/usr/bin/python
#
# 2017 Graham R Pugh
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
"""See docstring for Java6Versioner class"""

from __future__ import absolute_import

import plistlib

from autopkglib import Processor, ProcessorError

__all__ = ["Java6Versioner"]


class Java6Versioner(Processor):
    """Provides version of Java SE 6 for macOS."""
    input_variables = {
        "info_path": {
            "required": True,
            "description": ("Path to Info.plist"),
        },
    }

    output_variables = {
        "version": {
            "description": ("The value of the JVMVersion key"),
        },
    }

    description = __doc__

    def get_version(self, info_path):
        """grab the version number"""
        javaVersionPlist = plistlib.readPlist(info_path)
        javaVersion = javaVersionPlist["JavaVM"]["JVMVersion"]
        return javaVersion

    def main(self):
        info_path = self.env.get('info_path')
        self.env['version'] = self.get_version(info_path)
        self.output('Latest Version found: %s' % self.env['version'])

if __name__ == '__main__':
    PROCESSOR = Java6Versioner()
    PROCESSOR.execute_shell()
