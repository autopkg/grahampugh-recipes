#!/usr/local/autopkg/python
#
# Copyright 2022 by Graham Pugh
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
"""See docstring for LargeFileSplitter class"""

import subprocess

from autopkglib import Processor  # pylint: disable=import-error


__all__ = ["LargeFileSplitter"]


class LargeFileSplitter(Processor):
    """
    Splits a large file into 1024 MB chunks. The file can be recompiled in
    a shell script using:
    /bin/cat chunk_* > recompiled_file[.suffix]

    See com.github.eth-its-recipes.pkg.CSDS for a use case
    """

    description = __doc__
    input_variables = {
        "large_file_path": {
            "required": True,
            "description": ("Path to a large file that should be split up"),
        },
        "parts_dir": {
            "required": True,
            "description": ("Directory to store the split file parts."),
        },
    }
    output_variables = {}

    def split(self, large_file_path, parts_dir):
        """Do the split"""
        split_cmd = [
            "/usr/bin/split",
            "-b",
            "1024m",
            large_file_path,
            f"{parts_dir}/chunk_",
        ]
        # run the command
        subprocess.run(split_cmd)

    def main(self):
        """Split that file!"""
        large_file_path = self.env.get("large_file_path")
        parts_dir = self.env.get("parts_dir")
        self.split(large_file_path, parts_dir)


if __name__ == "__main__":
    PROCESSOR = LargeFileSplitter()
    PROCESSOR.execute_shell()
