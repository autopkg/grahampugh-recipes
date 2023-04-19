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

import os

from autopkglib import Processor

__all__ = ["GetUserHome"]


class GetUserHome(Processor):
    """
    This processor returns the current user's Home Directory.
    """

    input_variables = {}
    output_variables = {}

    description = __doc__

    def main(self):
        """Main process."""
        try:
            user_home = os.path.expanduser("~")
            current_user = os.path.basename(user_home)
            self.env["user_home"] = user_home
            self.env["current_user"] = current_user
            self.output(f"Current user: {current_user}")
            self.output(f"User Home Directory: {user_home}")
        except Exception as e:
            self.output(f"User Home Directory could not be determined (error: {e})")


if __name__ == "__main__":
    PROCESSOR = GetUserHome()
    PROCESSOR.execute_shell()
