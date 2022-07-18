#!/usr/bin/env python
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

from time import sleep

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["Sleep"]


class Sleep(Processor):
    """This processor replaces a string within a variable with another string.
    Example would be to remove a file suffix from a string:
    input_string: "filename.dmg"
    string_to_replace: ".dmg"
    replacement_string: ""
    output_string: "filename"
    """

    input_variables = {
        "sleep_time": {
            "required": False,
            "description": "The number of seconds to sleep.",
            "default": "5",
        },
    }
    output_variables = {}

    description = __doc__

    def main(self):
        """Main process."""
        sleep_time = self.env.get("sleep_time")
        sleep(sleep_time)


if __name__ == "__main__":
    PROCESSOR = Sleep()
    PROCESSOR.execute_shell()
