#!/usr/local/autopkg/python

"""
JamfCloudPackageUploader processor for AutoPkg
    by G Pugh

Developed from an idea posted at
    https://www.jamf.com/jamf-nation/discussions/27869#responseChild166021
"""


import argparse
import getpass
import sys
import os
import json
import base64
from xml.dom import minidom
import requests
import plistlib
from autopkglib import Processor, ProcessorError


class JamfCloudPackageUploader(Processor):
    """A post-processor for AutoPkg that will upload a package to a JCDS.
    Should be run as a post-processor for a pkg recipe. The pkg recipe
    must output pkg_path or this will fail."""

    input_variables = {
        "pkg_path": {
            "required": True,
            "description": "Path to a pkg or dmg to import - provided by "
            "previous pkg recipe/processor.",
            "default": "",
        },
        "replace_pkg": {
            "required": False,
            "description": "Overwrite an existing package if True.",
            "default": False,
        },
        "JSS_URL": {
            "required": True,
            "description": "URL to a Jamf Pro server that the API user has write access "
            "to, optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "API_USERNAME": {
            "required": True,
            "description": "Username of account with appropriate access to "
            "jss, optionally set as a key in the com.github.autopkg "
            "preference file.",
        },
        "API_PASSWORD": {
            "required": True,
            "description": "Password of api user, optionally set as a key in "
            "the com.github.autopkg preference file.",
        },
    }

    output_variables = {
        "version": {"description": ("The current package version."),},
        "CATEGORY": {"description": ("The package category."),},
        "SELF_SERVICE_DESCRIPTION": {"description": ("The self-service description."),},
        "pkg_path": {"description": ("the package path."),},
    }

    description = __doc__

    def check_pkg(self, pkg_name, jamf_url, enc_creds, replace_pkg):
        """check if a package with the same name exists in the repo
        note that it is possible to have more than one with the same name
        which could mess things up"""
        headers = {
            "authorization": "Basic {}".format(enc_creds),
            "accept": "application/json",
        }
        url = "{}/JSSResource/packages/name/{}".format(jamf_url, pkg_name)
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            obj = json.loads(r.text)
            try:
                obj_id = str(obj["package"]["id"])
                self.output("Existing Package Object ID found: {}".format(obj_id))
                if not replace_pkg:
                    self.output(
                        "Not replacing existing package. Set 'replace_pkg' to True to force upload."
                    )
                    return
            except KeyError:
                self.output("Existing Package Object ID found: {}".format(obj_id))
                obj_id = "-1"
        elif r.status_code == 404:
            self.output("Package is not already on the server")
            obj_id = "-1"
        else:
            self.output("HTTP GET Response Code: {}".format(r.status_code))
            obj_id = "-1"
        return obj_id

    def post_pkg(self, pkg_name, pkg_path, jamf_url, enc_creds, replace_pkg):
        """sends the package"""
        # check for existing
        obj_id = self.check_pkg(pkg_name, jamf_url, enc_creds, replace_pkg)

        if obj_id:
            self.output("Uploading '{}'".format(pkg_name))
            files = {"file": open(pkg_path, "rb")}
            headers = {
                "authorization": "Basic {}".format(enc_creds),
                "content-type": "application/xml",
                "DESTINATION": "0",
                "OBJECT_ID": obj_id,
                "FILE_TYPE": "0",
                "FILE_NAME": pkg_name,
            }
            url = "{}/dbfileupload".format(jamf_url)
            r = requests.post(url, files=files, headers=headers)
            return r

    def main(self):
        """Do the main thing here"""

        self.pkg_path = self.env.get("pkg_path")
        self.replace_pkg = self.env.get("replace_pkg")
        self.jamf_url = self.env.get("JSS_URL")
        self.jamf_user = self.env.get("API_USERNAME")
        self.jamf_password = self.env.get("API_PASSWORD")

        # encode the username and password into a basic auth b64 encoded string
        credentials = "%s:%s" % (self.jamf_user, self.jamf_password)
        enc_creds_bytes = base64.b64encode(credentials.encode("utf-8"))
        enc_creds = str(enc_creds_bytes, "utf-8")

        # now upload the package
        pkg_name = os.path.basename(self.pkg_path)
        self.output("Checking '{}' on {}".format(pkg_name, self.jamf_url))
        r = self.post_pkg(
            pkg_name, self.pkg_path, self.jamf_url, enc_creds, self.replace_pkg
        )

        # print result from the request
        if r:
            if r.status_code == 200 or r.status_code == 201:
                self.output("Package uploaded successfully")
            else:
                self.output("HTTP POST Response Code: {}".format(r.status_code))


if __name__ == "__main__":
    PROCESSOR = JamfCloudPackageUploader()
    PROCESSOR.execute_shell()
