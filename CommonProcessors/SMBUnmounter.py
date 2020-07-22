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

See docstring for SMBUnmounter class
"""

from __future__ import absolute_import
import os.path
import subprocess
from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["SMBUnmounter"]


class SMBUnmounter(Processor):
    """Unmounts an SMB share. Requires a mount point to be passed through from SMBMounter"""

    input_variables = {
        "mount_point": {"description": "Mount Point.", "required": True,},
    }

    output_variables = {}

    description = __doc__

    def unmount_smb_share(self, mount_point):
        """Unmount the smb share"""
        if os.path.exists(mount_point):
            cmd = [
                "/sbin/umount",
                mount_point,
            ]

            # unmount the share
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (cmd_out, cmd_err) = proc.communicate()
            if cmd_out:
                self.output(f"Result:\n{cmd_out.decode('ascii')}")
                self.output(f"{mount_point} unmounted")
            elif cmd_err:
                raise ProcessorError(cmd_err.decode("ascii"))

        # delete the mount folder
        cmd = [
            "/bin/rm",
            "-rf",
            mount_point,
        ]

        if os.path.exists(mount_point):
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (cmd_out, cmd_err) = proc.communicate()
            if cmd_out:
                self.output(f"Result:\n{cmd_out.decode('ascii')}")
            elif cmd_err:
                raise ProcessorError(cmd_err.decode("ascii"))

    def main(self):
        """do the main thing"""
        self.unmount_smb_share(self.env.get("mount_point"))


if __name__ == "__main__":
    PROCESSOR = SMBUnmounter()
    PROCESSOR.execute_shell()
