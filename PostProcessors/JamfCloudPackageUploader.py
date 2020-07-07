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
from time import sleep
from zipfile import ZipFile, ZIP_DEFLATED
import requests
import plistlib
import xml.etree.ElementTree as ElementTree
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
        "category": {
            "required": False,
            "description": "Package category",
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

    def check_pkg(self, pkg_name, jamf_url, enc_creds):
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
            except KeyError:
                obj_id = "-1"
        else:
            obj_id = "-1"
        return obj_id

    def post_pkg(self, pkg_name, pkg_path, jamf_url, enc_creds, obj_id):
        """sends the package"""
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

        http = requests.Session()
        r = http.post(url, files=files, headers=headers, timeout=3600)
        return r

    def update_pkg_metadata(self, jamf_url, enc_creds, pkg_name, category, pkg_id=None):
        """Update package metadata. Currently only serves category"""

        # build the package record XML
        pkg_data = (
            "<package>" + "<category>{}</category>".format(category) + "</package>"
        )
        headers = {
            "authorization": "Basic {}".format(enc_creds),
            "Accept": "application/xml",
            "Content-type": "application/xml",
        }
        #  ideally we upload to the package ID but if we didn't get a good response
        #  we fall back to the package name
        if pkg_id:
            url = "{}/JSSResource/packages/id/{}".format(jamf_url, pkg_id)
        else:
            url = "{}/JSSResource/packages/name/{}".format(jamf_url, pkg_name)

        http = requests.Session()

        self.output("Updating package metadata...")

        count = 0
        while True:
            count += 1
            self.output(f"Package update attempt {count}", verbose_level=2)

            r = http.put(url, headers=headers, data=pkg_data, timeout=60)
            if r.status_code == 201:
                self.output("Package update successful")
                break
            if count > 5:
                self.output("Package update did not succeed")
                self.output(
                    f"HTTP POST Response Code: {r.status_code}", verbose_level=2
                )
            sleep(30)

    def main(self):
        """Do the main thing here"""

        self.pkg_path = self.env.get("pkg_path")
        self.version = self.env.get("version")
        self.category = self.env.get("category")
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

        # now start the process of uploading the package
        self.output(f"Checking '{pkg_name}' on {self.jamf_url}")

        # check for existing
        obj_id = self.check_pkg(pkg_name, self.jamf_url, enc_creds)
        if obj_id == "-1" or self.replace_pkg:
            # post the package (won't run if the pkg exists and replace_pkg is False)
            r = self.post_pkg(pkg_name, self.pkg_path, self.jamf_url, enc_creds, obj_id)

            # print result of the request
            if r.status_code == 200 or r.status_code == 201:
                pkg_id = ElementTree.fromstring(r.text).findtext("id")
                self.output(f"Package uploaded successfully, ID={pkg_id}")
                #  now process the package metadata if specified
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

            #  now process the package metadata if specified
            if self.category:
                try:
                    pkg_id
                    self.update_pkg_metadata(
                        self.jamf_url, enc_creds, pkg_name, self.category, pkg_id
                    )
                except UnboundLocalError:
                    self.update_pkg_metadata(
                        self.jamf_url, enc_creds, pkg_name, self.category
                    )

        # output the summary
        self.env["pkg_path"] = self.pkg_path
        self.env["jamfcloudpackageuploader_summary_result"] = {
            "summary_text": "The following packages were uploaded:",
            "report_fields": ["pkg_path", "pkg_name", "version", "category"],
            "data": {
                "pkg_path": self.pkg_path,
                "pkg_name": pkg_name,
                "version": self.version,
                "category": self.category,
            },
        }


if __name__ == "__main__":
    PROCESSOR = JamfCloudPackageUploader()
    PROCESSOR.execute_shell()
