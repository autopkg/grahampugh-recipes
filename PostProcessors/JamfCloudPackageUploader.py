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
from zipfile import ZipFile, ZIP_DEFLATED
import requests
import plistlib
from autopkglib import Processor, ProcessorError


class JamfCloudPackageUploader(Processor):
    """A post-processor for AutoPkg that will upload a package to a JCDS.
    Should be run as a post-processor for a pkg recipe. The pkg recipe
    must output pkg_path or this will fail."""

    input_variables = {
        "pkg_path": {
            "required": False,
            "description": "Path to a pkg or dmg to import - provided by "
            "previous pkg recipe/processor.",
            "default": "",
        },
        "version": {
            "required": False,
            "description": "Version string - provided by "
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
        "pkg_path": {"description": "The created package.",},
        "jamfcloudpackageuploader_summary_result": {
            "description": "Description of interesting results.",
        },
    }

    description = __doc__

    def check_pkg(self, pkg_name, jamf_url, enc_creds, replace_pkg):
        """check if a package with the same name exists in the repo
        note that it is possible to have more than one with the same name
        which could mess things up"""
        headers = {
            "authorization": f"Basic {enc_creds}",
            "accept": "application/json",
        }
        url = f"{jamf_url}/JSSResource/packages/name/{pkg_name}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            obj = json.loads(r.text)
            try:
                obj_id = str(obj["package"]["id"])
                self.output(f"Existing Package Object ID found: {obj_id}")
                if not replace_pkg:
                    self.output(
                        "Not replacing existing package. Set 'replace_pkg' to True to force upload."
                    )
                    return
            except KeyError:
                self.output(f"Existing Package Object ID found: {obj_id}")
                obj_id = "-1"
        elif r.status_code == 404:
            self.output("Package is not already on the server")
            obj_id = "-1"
        else:
            self.output(f"HTTP GET Response Code: {r.status_code}")
            obj_id = "-1"
        return obj_id

    def zip_pkg_path(self, path):
        """Add files from path to a zip file handle.

        Args:
            path (str): Path to folder to zip.

        Returns:
            (str) name of resulting zip file.
        """
        zip_name = f"{path}.zip"

        if os.path.exists(zip_name):
            self.output("Package object is a bundle. Zipped version already exists.")
            return zip_name

        self.output("Package object is a bundle. Converting to zip...")
        with ZipFile(zip_name, "w", ZIP_DEFLATED, allowZip64=True) as zip_handle:
            for root, _, files in os.walk(path):
                for member in files:
                    zip_handle.write(os.path.join(root, member))
            self.output(
                f"Closing: {zip_name}", verbose_level=2,
            )
        return zip_name

    def post_pkg(self, pkg_name, pkg_path, jamf_url, enc_creds, replace_pkg):
        """sends the package"""
        # check for existing
        obj_id = self.check_pkg(pkg_name, jamf_url, enc_creds, replace_pkg)

        if obj_id:
            self.output(f"Uploading '{pkg_name}'")
            files = {"file": open(pkg_path, "rb")}
            headers = {
                "authorization": f"Basic {enc_creds}",
                "content-type": "application/xml",
                "DESTINATION": "0",
                "OBJECT_ID": obj_id,
                "FILE_TYPE": "0",
                "FILE_NAME": pkg_name,
            }
            url = f"{jamf_url}/dbfileupload"
            r = requests.post(url, files=files, headers=headers)
            return r

    def main(self):
        """Do the main thing here"""

        self.pkg_path = self.env.get("pkg_path")
        self.version = self.env.get("version")
        self.replace_pkg = self.env.get("replace_pkg")
        self.jamf_url = self.env.get("JSS_URL")
        self.jamf_user = self.env.get("API_USERNAME")
        self.jamf_password = self.env.get("API_PASSWORD")
        # clear any pre-existing summary result
        if "jamfcloudpackageuploader_summary_result" in self.env:
            del self.env["jamfcloudpackageuploader_summary_result"]

        # encode the username and password into a basic auth b64 encoded string
        credentials = "%s:%s" % (self.jamf_user, self.jamf_password)
        enc_creds_bytes = base64.b64encode(credentials.encode("utf-8"))
        enc_creds = str(enc_creds_bytes, "utf-8")

        pkg_name = os.path.basename(self.pkg_path)
        # See if the package is non-flat (requires zipping prior to upload).
        if os.path.isdir(self.pkg_path):
            self.pkg_path = self.zip_pkg_path(self.pkg_path)
            pkg_name += ".zip"

        # now upload the package
        self.output(f"Checking '{pkg_name}' on {self.jamf_url}")
        r = self.post_pkg(
            pkg_name, self.pkg_path, self.jamf_url, enc_creds, self.replace_pkg
        )

        # print result of the request
        if r.status_code == 200 or r.status_code == 201:
            self.output("Package uploaded successfully")
        else:
            self.output("An error occurred while attempting to upload the package")
            self.output(
                f"HTTP POST Response Code: {r.status_code}", verbose_level=2,
            )
            self.output(
                "\nHeaders:\n", verbose_level=2,
            )
            self.output(
                r.headers, verbose_level=2,
            )
            self.output(
                "\nResponse:\n", verbose_level=2,
            )
            if r.text:
                self.output(
                    r.text, verbose_level=2,
                )
            else:
                self.output(
                    "None", verbose_level=2,
                )

            # output the summary
            self.env["pkg_path"] = self.pkg_path
            self.env["jamfcloudpackageuploader_summary_result"] = {
                "summary_text": "The following packages were uploaded:",
                "report_fields": ["pkg_path", "pkg_name", "version"],
                "data": {
                    "pkg_path": self.pkg_path,
                    "pkg_name": pkg_name,
                    "version": self.version,
                },
            }


if __name__ == "__main__":
    PROCESSOR = JamfCloudPackageUploader()
    PROCESSOR.execute_shell()
