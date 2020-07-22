#!/usr/bin/python
#
# Copyright 2013 Jesse Peterson
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

import os

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["SubDirectoryList"]


class SubDirectoryList(Processor):
    """Finds a filename for use in other Processors.
    Currently only supports glob filename patterns.
    """

    input_variables = {
        "root_path": {
            "description": "Path to start looking for files.",
            "required": True,
        },
        "suffix_string": {
            "description": (
                "String to append to each found item name in dir." "Defaults to ','"
            ),
            "default": ",",
            "required": False,
        },
        "max_depth": {
            "description": ("maximum depth of folders to iterate through"),
            "default": "2",
            "required": False,
        },
        "LANGUAGE": {
            "required": False,
            "description": (
                "Language of the pkg or DMG containing PKG," "one of ML, DE, EN."
            ),
            "default": "",
        },
        "LICENSE": {
            "required": False,
            "description": (
                "License of the pkg or DMG containing PKG," "one of Floating, Node."
            ),
            "default": "",
        },
        "EXCEPTION": {
            "required": False,
            "description": ("A variable to exclude from the search"),
            "default": "",
        },
        "LIMITATION": {
            "required": False,
            "description": ("A variable to require in the search"),
            "default": "",
        },
    }
    output_variables = {
        "found_filenames": {
            "description": (
                "String containing a list of all files found "
                "relative to root_path, separated by "
                "suffix_string."
            )
        },
        "relative_root": {"description": ("Relative root path")},
    }

    description = __doc__

    def walk(self, top, maxdepth):
        dirs, nondirs = [], []
        for name in os.listdir(top):
            (dirs if os.path.isdir(os.path.join(top, name)) else nondirs).append(name)
        yield top, dirs, nondirs
        if maxdepth > 1:
            for name in dirs:
                for x in self.walk(os.path.join(top, name), maxdepth - 1):
                    yield x

    def main(self):
        sip_dirs = ["usr", "usr/local", "private", "private/etc", "Library"]
        format_string = self.env["suffix_string"]
        dmg_language = self.env["LANGUAGE"]
        dmg_license = self.env["LICENSE"]
        dmg_exception = self.env["EXCEPTION"]
        dmg_limitation = self.env["LIMITATION"]
        search_string = "{0}"
        dir_list = list()
        file_list = list()
        if not os.path.isdir(self.env["root_path"]):
            raise ProcessorError("Can't find root path!")
        for dirName, subdirList, fileList in self.walk(
            self.env["root_path"], int(self.env["max_depth"])
        ):
            relative_path = os.path.relpath(dirName, self.env["root_path"])
            # We need to remove the SIP folders so Chef doesn't try to create them
            if not relative_path == "." and not (relative_path in sip_dirs):
                dir_list.append(relative_path)
            for fname in fileList:
                if ".DS_Store" in fname:
                    continue
                relpath = os.path.relpath(
                    os.path.join(fname, dirName), self.env["root_path"]
                )
                self.output(f"Relative path: {relpath}")
                self.output(f"Filename: {fname}")
                if dmg_language and (dmg_language not in fname):
                    continue
                if dmg_license and (dmg_license not in fname):
                    continue
                if dmg_exception and (dmg_exception in fname):
                    continue
                if dmg_limitation and (dmg_limitation not in fname):
                    continue
                if relpath == ".":
                    # we want to avoid prepending './' to files at root dir
                    relpath = ""
                file_list.append(os.path.join(relpath, fname))
        self.env["found_directories"] = search_string.format(
            format_string.join(dir_list)
        ).strip()
        self.env["found_filenames"] = search_string.format(
            format_string.join(file_list)
        ).strip()


if __name__ == "__main__":
    PROCESSOR = SubDirectoryList()
    PROCESSOR.execute_shell()
