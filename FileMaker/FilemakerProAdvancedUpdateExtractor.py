#!/usr/bin/python
# FilemakerProAdvancedUpdateDMGExtractor.py
# Extracts a FileMaker updater package from a given DMG.
#
# Copyright 2016 William McGrath
# w.mcgrath@auckland.ac.nz
#
# Licensed under the Apache License, version 2.0 (the "License"). You
# may not use this file except in compliance with the
# License.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#



"""See docstring for FilemakerProAdvancedUpdateDMGExtractor class"""

from __future__ import absolute_import

import fnmatch
import os
import shutil
import zipfile

from autopkglib import Processor, ProcessorError
from autopkglib.DmgMounter import DmgMounter

__all__ = ["FilemakerProAdvancedUpdateExtractor"]

class FilemakerProAdvancedUpdateExtractor(DmgMounter):
    """Extracts update pkg from given DMG or ZIP"""

    description = __doc__
    input_variables = {
        "downloaded_file": {
            "required": True,
            "description":
                "The path to the DMG or ZIP downloaded from the FileMaker website"
        }
    }
    output_variables = {
        "extracted_pkg": {
            "description": "Outputs the extracted package path."
        }
    }
    def find_pkg(self, dir_path):
        '''Return path to the first package in dir_path'''
        #pylint: disable=no-self-use
        for item in os.listdir(dir_path):
            if item.endswith(".pkg"):
                return os.path.join(dir_path, item)
        raise ProcessorError("No package found in %s" % dir_path)

    def is_zip(self, path_to_download):
        filename, file_extension = os.path.splitext(path_to_download)
        if file_extension == ".zip":
            return True
        return False

    def main(self):
        if self.is_zip(self.env["downloaded_file"]):
            try:
                with zipfile.ZipFile(self.env["downloaded_file"], 'r') as zf:
                    contents = zf.namelist()
                    pkgs = [f for f in contents if fnmatch.fnmatch(f, '*.pkg')]
                    zf.extract(pkgs[0], self.env["RECIPE_CACHE_DIR"])
                    self.env["extracted_pkg"] = os.path.join(self.env["RECIPE_CACHE_DIR"], os.path.basename(pkgs[0]))
            except Exception as err:
                raise ProcessorError(err)
        else:
            mount_point = self.mount(self.env["downloaded_file"])
            # Wrap all other actions in a try/finally so the image is always
            # unmounted.
            try:
                pkg = self.find_pkg(mount_point)
                shutil.copy(pkg, self.env['RECIPE_CACHE_DIR'])
                self.env["extracted_pkg"] = os.path.join(self.env['RECIPE_CACHE_DIR'], os.path.basename(pkg))
            except Exception as err:
                raise ProcessorError(err)
            finally:
                self.unmount(self.env["downloaded_file"])

if __name__ == "__main__":
    PROCESSOR = FilemakerProAdvancedUpdateExtractor()
    PROCESSOR.execute_shell()
