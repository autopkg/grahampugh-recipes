#!/usr/local/autopkg/python
#
# Copyright 2023 Graham Pugh
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

import subprocess

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["BinaryVersioner"]


class BinaryVersioner(Processor):
    """find the version of a binary by running it with an appropriate parameter.
    Requires path to desired binary and exactly one parameter to pass to it."""

    input_variables = {
        "binary_path": {
            "required": True,
            "description": "Path to the binary.",
        },
        "binary_parameter": {
            "required": True,
            "description": "A parameter to run the binary with, for example '--version'.",
        },
    }
    output_variables = {
        "version": {
            "description": "binary version.",
        },
    }

    description = __doc__

    def main(self):
        """Main process."""
        self.binary_path = self.env.get("binary_path")
        self.binary_parameter = self.env.get("binary_parameter")

        cmd = [
            self.binary_path,
            self.binary_parameter,
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sout, serr = proc.communicate()

        if sout:
            # the output includes a newline so needs to be stripped of it
            version = sout.decode('ascii').rstrip()
            self.env["version"] = version
            self.output(f"Version found: {version}")
        elif serr:
            raise ProcessorError("Error: Version not found")


if __name__ == "__main__":
    PROCESSOR = BinaryVersioner()
    PROCESSOR.execute_shell()
