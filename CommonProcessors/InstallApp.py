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
"""See docstring for InstallApp class"""

import os.path
import plistlib
import socket

from autopkglib import Processor, ProcessorError

AUTOPKGINSTALLD_SOCKET = "/var/run/autopkginstalld"


__all__ = ["InstallApp"]


class InstallApp(Processor):
    """Calls autopkginstalld to copy an application to the root filesystem."""

    description = __doc__
    input_variables = {
        "app_path": {
            "required": True,
            "description": "Path to the folder containing the app bundle.",
        },
        "items_to_copy": {
            "required": True,
            "description": (
                "Array of dictionaries describing what is to be copied. "
                "Each item should contain 'source_item' and "
                "'destination_path', and may optionally include: "
                "'destination_item' to rename the item on copy, and "
                "'user', 'group' and 'mode' to explicitly set those items."
            ),
        },
        "download_changed": {
            "required": False,
            "description": (
                "download_changed is set by the URLDownloader processor to "
                "indicate that a new file was downloaded. If this key is set "
                "in the environment and is False or empty the installation "
                "will be skipped."
            ),
        },
    }
    output_variables = {
        "install_result": {"description": "Result of install request."},
        "install_app_summary_result": {
            "description": "Description of interesting results."
        },
    }

    def install(self):
        """Build an ItemCopier request, send it to autopkginstalld"""
        # clear any pre-existing summary result
        if "install_app_summary_result" in self.env:
            del self.env["install_app_summary_result"]

        if "download_changed" in self.env:
            if not self.env["download_changed"]:
                # URLDownloader did not download something new,
                # so skip the install
                self.output("Skipping installation: no new download.")
                self.env["install_result"] = "SKIPPED"
                return
        try:
            app_path = self.env["app_path"]

            request = {
                "mount_point": app_path,
                "items_to_copy": self.env["items_to_copy"],
            }
            result = None
            # Send install request.
            try:
                self.output("Connecting")
                self.connect()
                self.output("Sending installation request")
                self.output(
                    "[TEMP] Item: {}".format(
                        self.env["items_to_copy"][0]["source_item"]
                    ),
                    verbose_level=2,
                )

                result = self.send_request(request)
            except Exception as err:
                result = f"ERROR: {err}"
            finally:
                self.output("Disconnecting")
                self.disconnect()

            # Return result.
            self.output(f"Result: {result}")
            self.env["install_result"] = result
            if result == "DONE":
                self.env["install_app_summary_result"] = {
                    "summary_text": (
                        "The following items " "were successfully installed:"
                    ),
                    "data": {"app_path": self.env["items_to_copy"][0]["source_item"]},
                }
        except Exception as err:
            result = f"ERROR: {err}"

    def connect(self):
        """Connect to autopkginstalld"""
        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(AUTOPKGINSTALLD_SOCKET)
        except OSError as err:
            raise ProcessorError(f"Couldn't connect to autopkginstalld: {err.strerror}")

    def send_request(self, request):
        """Send an install request to autopkginstalld"""
        self.socket.send(plistlib.dumps(request))
        with os.fdopen(self.socket.fileno()) as fileref:
            while True:
                data = fileref.readline()
                if data:
                    if data.startswith("OK:"):
                        return data.replace("OK:", "").rstrip()
                    elif data.startswith("ERROR:"):
                        break
                    else:
                        self.output(data.rstrip())
                else:
                    break

        errors = data.rstrip().split("\n")
        if not errors:
            errors = ["ERROR:No reply from autopkginstalld (crash?), check system logs"]
        raise ProcessorError(", ".join([s.replace("ERROR:", "") for s in errors]))

    def disconnect(self):
        """Disconnect from autopkginstalld"""
        try:
            self.socket.close()
        except OSError:
            # the socket is already closed
            pass

    def main(self):
        """Install something!"""
        self.install()


if __name__ == "__main__":
    PROCESSOR = InstallApp()
    PROCESSOR.execute_shell()
