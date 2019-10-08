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

import plistlib
import sys

from distutils.version import LooseVersion
from os.path import expanduser, getmtime, exists
from autopkglib import Processor, ProcessorError
from glob import iglob


__all__ = ["JSSRecipeReceiptChecker"]


class JSSRecipeReceiptChecker(Processor):
    """An AutoPkg processor which works out the latest receipt from a different AutoPkg recipe, and provides useful values from its contents, which can be used to run a different recipe based on those values."""
    input_variables = {
        'name': {
            'description': 'This value should be the same as the NAME in the recipe from which we want to read the receipt. This is all we need to construct the override path.',
            'required': True,
        },
        'cache_dir': {
            'description': 'Path to the cache dir.',
            'required': False,
            'default': '~/Library/AutoPkg/Cache'
        },
    }

    output_variables = {
        "version": {
            "description": ("The current package version."),
        },
        "CATEGORY": {
            "description": ("The package category."),
        },
        "SELF_SERVICE_DESCRIPTION": {
            "description": ("The self-service description."),
        },
        "pkg_path": {
            "description": ("the package path."),
        },
    }

    description = __doc__

    def get_latest_receipt(self, cache_dir, name, n):
        """name of receipt with the highest version number"""
        files = list(iglob('{}/local.jss.{}/receipts/*.plist'.format(cache_dir, name)))
        files.sort(key=lambda x: getmtime(x), reverse=True)
        return files[n]

    def main(self):
        name = self.env.get('name')
        cache_dir = expanduser(self.env.get('cache_dir'))
        version_found = False

        n = 0
        while not version_found:
            try:
                receipt = self.get_latest_receipt(cache_dir, name, n)
            except IOError:
                raise ProcessorError('No receipt found!')

            self.output('Receipt: {}'.format(receipt))

            p = plistlib.readPlist(receipt)
            i = 0
            while i < len(p):
                try:
                    processor = p[i]['Processor']
                    if processor == 'JSSImporter':
                        version = p[i]['Input']['version']
                        pkg_path = p[i]['Input']['pkg_path']
                        CATEGORY = p[i]['Input']['category']
                        SELF_SERVICE_DESCRIPTION = (
                                    p[i]['Input']['self_service_description'])
                except KeyError:
                    pass
                i = i + 1

            # make sure all the values were obtained from the receipt
            try:
                self.env['version'] = version
                self.env['pkg_path'] = pkg_path
                self.env['CATEGORY'] = CATEGORY
                self.env['SELF_SERVICE_DESCRIPTION'] = (
                         SELF_SERVICE_DESCRIPTION)
                break
            except:
                # we should specify a specific error here but not sure which
                # try UnboundLocalError
                self.output('No JSSImporter process found in receipt')
                n = n + 1
                # raise ProcessorError('No JSSImporter process found in receipt')

        # make sure the package actually exists
        if not exists(pkg_path):
            raise ProcessorError('Package does not exist: {}'.format(pkg_path))

        self.output('Package: {}'.format(pkg_path))
        self.output('Version: {}'.format(version))
        self.output('Category: {}'.format(CATEGORY))
        self.output('Self Service Description: {}'.format(
                    SELF_SERVICE_DESCRIPTION))
        # end

if __name__ == '__main__':
    PROCESSOR = JSSRecipeReceiptChecker()
    PROCESSOR.execute_shell()
