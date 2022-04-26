#!/usr/bin/env python
"""Intellij URL Provider."""
# Copyright (c) Facebook, Inc. and its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import xml.etree.cElementTree as ET

from autopkglib.URLGetter import URLGetter


__all__ = ["IntellijURLProvider"]

intellij_version_url = "https://www.jetbrains.com/updates/updates.xml"


class IntellijURLProvider(URLGetter):
    """Provide URL for latest Intellij IDEA build."""

    description = "Provides URL and version for the latest release of Intellij."
    input_variables = {
        "base_url": {
            "required": False,
            "description": (
                "Default is " "https://www.jetbrains.com/updates/updates.xml"
            ),
        },
        "edition": {
            "required": False,
            "description": (
                'Either "C" for "Community" or "U" for "Ultimate" '
                'edition. Defaults to "C".'
            ),
        },
    }
    output_variables = {"url": {"description": "URL to the latest release of Intellij"}}

    __doc__ = description

    def get_intellij_version(self, intellij_version_url):
        """Retrieve version number from XML."""
        # Read XML
        raw_xml = self.download(intellij_version_url, text=True)
        # Select the latest released build
        root = ET.fromstring(raw_xml)
        product = root.find('product[@name="IntelliJ IDEA"]')
        channel = product.find('channel[@status="release"]')
        builds = channel.findall("build")
        version = builds[0].attrib["version"]
        # Return pkg url.
        return str(version)

    def main(self):
        """Main function."""
        # Determine values.
        version_url = self.env.get("version_url", intellij_version_url)
        version = self.get_intellij_version(version_url)
        download_url = "https://download.jetbrains.com/idea/" "ideaI%s-%s.dmg" % (
            self.env.get("edition", "C"),
            version,
        )

        self.env["url"] = download_url
        self.output("URL: %s" % self.env["url"])


if __name__ == "__main__":
    processor = IntellijURLProvider()
    processor.execute_shell()
