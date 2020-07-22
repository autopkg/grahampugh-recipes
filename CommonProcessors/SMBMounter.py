#!/usr/bin/python

"""
2020 Graham R Pugh

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

See docstring for SMBMounter class
"""

from __future__ import absolute_import
import os
import subprocess
from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["SMBMounter"]


class SMBMounter(Processor):
    """Mounts an SMB share."""

    input_variables = {
        "smb_path": {
            "description": "Repo smb path. This must be the full path starting"
            "with // and including any domains and credentials.",
            "required": True,
        },
        "mount_point": {
            "description": "Mount Point.",
            "required": False,
            "default": "/tmp/tmp_autopkg_mount",
        },
    }

    output_variables = {
        "mount_point": {"description": "Mount Point."},
    }

    description = __doc__

    def mount_smb_share(self, smb_path, mount_point):
        """Mount the smb share"""
        if not os.path.exists(mount_point):
            os.makedirs(mount_point)

        cmd = [
            "/sbin/mount",
            "-t",
            "smbfs",
            smb_path,
            mount_point,
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (cmd_out, cmd_err) = proc.communicate()
        if cmd_out:
            self.output(f"Result:\n{cmd_out.decode('ascii')}")
        elif cmd_err:
            self.output(
                f"Share is probably already mounted. Result:\n{cmd_err.decode('ascii')}"
            )
        else:
            self.output(f"{mount_point} mounted")

    def main(self):
        """do the main thing"""
        smb_path = self.env.get("smb_path")
        mount_point = self.env.get("mount_point")

        self.mount_smb_share(smb_path, mount_point)


if __name__ == "__main__":
    PROCESSOR = SMBMounter()
    PROCESSOR.execute_shell()
