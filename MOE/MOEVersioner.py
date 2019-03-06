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
"""See docstring for moeVersioner class"""

import subprocess
import plistlib
from autopkglib import Processor, ProcessorError

__all__ = ["moeVersioner"]


class moeVersioner(Processor):
    """Provides version of Moe for macOS."""
    input_variables = {
        "info_path": {
            "required": True,
            "description": ("Path to Info.plist"),
        },
    }

    output_variables = {
        "version": {
            "description": ("The version of MOE from CFBundleName"),
        },
    }

    description = __doc__

    def get_version(self, info_path):
        """grab the version number"""
        moeVersionPlist = plistlib.readPlist(info_path)
        moeVersion = moeVersionPlist["CFBundleName"].split()
        return moeVersion[1]

    def main(self):
        info_path = self.env.get('info_path')
        self.env['version'] = self.get_version(info_path)
        self.output('Latest Version found: %s' % self.env['version'])

if __name__ == '__main__':
    PROCESSOR = moeVersioner()
    PROCESSOR.execute_shell()
