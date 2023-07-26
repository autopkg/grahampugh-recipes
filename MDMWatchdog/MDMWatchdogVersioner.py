#!/usr/local/autopkg/python
#
# Copyright 2022 Graham Pugh
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

__all__ = ["MDMWatchdogVersioner"]


class MDMWatchdogVersioner(Processor):
    """find the version of MDM Watchdog by running the binary"""

    input_variables = {
        "binary_path": {
            "required": True,
            "description": "Path to the mdm-watchdog binary.",
        },
    }
    output_variables = {
        "version": {
            "description": "mdm-watchdog version.",
        },
    }

    description = __doc__

    def main(self):
        """Main process."""
        self.binary_path = self.env.get("binary_path")

        cmd = [
            self.binary_path,
            "-version",
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
    PROCESSOR = MDMWatchdogVersioner()
    PROCESSOR.execute_shell()
