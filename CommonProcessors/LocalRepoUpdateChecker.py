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
"""See docstring for LocalRepoUpdateChecker class"""

import os, sys
import filecmp
from distutils.version import LooseVersion
from autopkglib import Processor, ProcessorError

__all__ = ["LocalRepoUpdateChecker"]


class LocalRepoUpdateChecker(Processor):
    """Provides file path to the highest version number."""
    input_variables = {
        'root_path': {
            'description': 'Repo path. Used here for comparisons.',
            'required': True,
        },
        "found_filenames": {
            "required": True,
            "description": ("Output of SubDirectoryList found_filenames."),
        },
        "RECIPE_CACHE_DIR": {
            "required": True,
            "description": ("AutoPkg Cache directory."),
        },
    }

    output_variables = {
        "version": {
            "description": ("The highest folder name according to "
                            "LooseVersion logic."),
        },
        "latest_file": {
            "description": ("The filename of the highest version according to "
                            "LooseVersion logic."),
        },
        "file_exists": {
            "description": ("Boolean to show whether the latest version is "
                            "already present in the AutoPkg Cache"),
        },
        "cached_path": {
            "description": ("Path to the existing file in the AutoPkg Cache "
                            "including filename"),
        },
    }

    description = __doc__

    def get_latest_version(self, found_filenames):
        """name of folder with the highest version number"""
        file_list = found_filenames.split(",")
        latest_version = "0"
        for item in file_list:
            item_version = item.split("/")[0]
            if LooseVersion(item_version) > LooseVersion(latest_version):
                latest_version = item_version
        return latest_version

    def get_latest_dmg(self, version):
        """path of file with the version number provided"""
        latest_file_relpath = ""
        file_list = self.env.get('found_filenames').split(",")
        for item in file_list:
            item_version = item.split("/")[0]
            if version in item_version:
                latest_file_relpath = item
        return latest_file_relpath

    def check_file_exists(self, repo_path, local_path):
        """Check if the file already exists in the AutoPkg cache"""
        # file_exists = False
        # if os.path.exists(file_path):
        #     file_exists = True
        file_exists = filecmp.cmp(repo_path, local_path)
        return file_exists

    def main(self):
        found_filenames = self.env.get('found_filenames')
        repo_path = self.env.get('root_path')
        RECIPE_CACHE_DIR = self.env.get('RECIPE_CACHE_DIR')
        downloads_dir = os.path.join(RECIPE_CACHE_DIR, 'downloads')

        self.env['version'] = self.get_latest_version(found_filenames)
        self.output('Latest Version found: %s' % self.env['version'])

        latest_file_relpath = self.get_latest_dmg(self.env['version'])
        latest_file_dmgname = latest_file_relpath.rsplit("/")[1]
        self.env['latest_file'] = latest_file_dmgname.rsplit(".", 1)[0]
        self.output('Filename of latest version: %s' % self.env['latest_file'])

        self.env['cached_path'] = os.path.join(downloads_dir, latest_file_dmgname)
        if os.path.exists(self.env['cached_path']):
            self.output('Path to file in cache: %s' % self.env['cached_path'])
            repo_path = os.path.join(repo_path, latest_file_relpath)
            self.env['file_exists'] = self.check_file_exists(self.env['cached_path'],repo_path)
            if self.env['file_exists'] == True:
                self.output('File %s is already in the AutoPkg Cache and up-to-date' % self.env['latest_file'])
            else:
                self.output('File %s is in the AutoPkg Cache but out of date' % self.env['latest_file'])
        else:
            self.output('File %s is not in the AutoPkg Cache' % self.env['latest_file'])
            self.env['file_exists'] = False
        # end

if __name__ == '__main__':
    PROCESSOR = LocalRepoUpdateChecker()
    PROCESSOR.execute_shell()
