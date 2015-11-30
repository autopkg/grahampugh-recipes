#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Adapted from "MunkiGitCommitter.py",
# Copyright 2015 Nathan Felton (n8felton)
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

import os, sys
import subprocess
import time
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from autopkglib import Processor, ProcessorError
from autopkglib import get_pref

__all__ = ["MunkiGitBranchingCommitter"]

# edit this if your production branch isn't "master"
PRODUCTION_BRANCH = "master"

class MunkiGitBranchingCommitter(Processor):
    description = "Allows AutoPkg to commit changes to a munki repository \
                   that is tracked by a git repository."
    input_variables = {
        "MUNKI_REPO": {
            "description": "Path to a mounted Munki repo.",
            "required": True
        },    
        "GIT_COMMIT_MESSAGE": {
            "required": False,
            "description": "Any additional message you want attached to the \
                            commit."
        },
        "munki_importer_summary_result": {
            "required": False,
            "description": "Stuff goes here"
        }
    }
    output_variables = {
    }

    def git_cmd(self):
        """Returns a path to a git binary, priority in the order below.
        Returns None if none found.
        1. app pref 'GIT_PATH'
        2. a 'git' binary that can be found in the PATH environment variable
        3. '/usr/bin/git'
        """

        def is_executable(exe_path):
            '''Is exe_path executable?'''
            return os.path.exists(exe_path) and os.access(exe_path, os.X_OK)

        git_path_pref = get_pref("GIT_PATH")
        if git_path_pref:
            if is_executable(git_path_pref):
                # take a GIT_PATH pref
                return git_path_pref
            else:
                logging.debug("WARNING: Git path given in the 'GIT_PATH' preference:"
                        " '%s' either doesn't exist or is not executable! "
                        "Falling back to one set in PATH, or /usr/bin/git."
                        % git_path_pref)
        for path_env in os.environ["PATH"].split(":"):
            gitbin = os.path.join(path_env, "git")
            if is_executable(gitbin):
                # take the first 'git' in PATH that we find
                return gitbin
        if is_executable("/usr/bin/git"):
            # fall back to /usr/bin/git
            return "/usr/bin/git"
        return None

    class GitError(Exception):
        '''Exception to throw if git fails'''
        pass

    def run_git(self, git_options_and_arguments, git_directory=None):
        '''Run a git command and return its output if successful;
           raise GitError if unsuccessful.'''
        gitcmd = self.git_cmd()
        if not gitcmd:
            logging.debug("ERROR: git is not installed!")
        cmd = [gitcmd]
        cmd.extend(git_options_and_arguments)
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=git_directory)
            (cmd_out, cmd_err) = proc.communicate()
        except OSError as err:
            logging.debug("ERROR: git execution failed with error code %d: %s"
                           % (err.errno, err.strerror))
        if proc.returncode != 0:
            logging.debug("ERROR: %s" % cmd_err)
        else:
            logging.debug("GIT CMD processed: %s" % cmd_out)
            return cmd_out

    def checkoutUserBranch(self):
        """Creates a new git branch with name autopkg_run_timestamp"""
        time_stamp = str(time.strftime('%Y%m%d%H%M%S'))
        branch_committer = "autopkg_run"
        seq = (branch_committer, time_stamp)
        s = "_"
        branch_name = s.join(seq)
        self.run_git(['checkout', '-b', branch_name],
                     git_directory=self.env["MUNKI_REPO"])
        return branch_name

    def checkoutProductionBranch(self):
        """Checkout the master/production branch"""
        self.run_git(['checkout', PRODUCTION_BRANCH],
                     git_directory=self.env["MUNKI_REPO"])
        self.run_git(['pull'],
                     git_directory=self.env["MUNKI_REPO"])

    def main(self):
        # If we did not import anything, skip trying to commit anything.
        # This also helps run MakeCatalogs.munki.recipe
        if not self.env.get('munki_importer_summary_result'):
            return

        pkginfo_path = '{0}/{1}'.format('pkgsinfo',
                                        self.env
                                        ['munki_importer_summary_result']
                                        ['data']
                                        ['pkginfo_path'])
        name = self.env['munki_importer_summary_result']['data']['name']
        version = self.env['munki_importer_summary_result']['data']['version']
        if self.env.get("GIT_COMMIT_MESSAGE"):
            commit_message = self.env.get('GIT_COMMIT_MESSAGE')
        else:
            commit_message = "[AutoPkg] Adding {0} version {1}". \
                             format(name, version)

        branch_name = self.checkoutUserBranch()
        self.run_git(['add', pkginfo_path],
                     git_directory=self.env["MUNKI_REPO"])
        self.run_git(['commit', '-m', commit_message],
                     git_directory=self.env["MUNKI_REPO"])
        self.run_git(['push', '--set-upstream', 'origin', branch_name],
                     git_directory=self.env["MUNKI_REPO"])
        self.checkoutProductionBranch()

if __name__ == "__main__":
    processor = MunkiGitBranchingCommitter()
    processor.execute_shell()
