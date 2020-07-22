#!/usr/bin/python
#
# Copyright 2017 Graham Pugh
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

from __future__ import absolute_import, print_function

import requests

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

# Set the webhook_url to the one provided by Slack when you create the webhook at https://my.slack.com/services/new/incoming-webhook/

__all__ = ["Slacker"]


class Slacker(Processor):
    description = (
        "Posts to Slack via webhook based on output of a JSSImporter run. "
        "Takes elements from "
        "https://gist.github.com/devStepsize/b1b795309a217d24566dcc0ad136f784"
        "and "
        "https://github.com/autopkg/nmcspadden-recipes/blob/master/PostProcessors/Yo.py"
    )
    input_variables = {
        "JSS_URL": {"required": False, "description": ("JSS_URL.")},
        "policy_category": {"required": False, "description": ("Policy Category.")},
        "category": {"required": False, "description": ("Package Category.")},
        "prod_name": {"required": False, "description": ("Title (NAME)")},
        "jss_changed_objects": {
            "required": False,
            "description": ("Dictionary of added or changed values."),
        },
        "jss_importer_summary_result": {
            "required": False,
            "description": ("Description of interesting results."),
        },
        "webhook_url": {"required": False, "description": ("Slack webhook.")},
    }
    output_variables = {}

    __doc__ = description

    def main(self):
        JSS_URL = self.env.get("JSS_URL")
        policy_category = self.env.get("policy_category")
        category = self.env.get("category")
        prod_name = self.env.get("prod_name")
        jss_changed_objects = self.env.get("jss_changed_objects")
        jss_importer_summary_result = self.env.get("jss_importer_summary_result")
        webhook_url = self.env.get("webhook_url")

        if jss_changed_objects:
            jss_policy_name = jss_importer_summary_result["data"]["Policy"]
            jss_policy_version = jss_importer_summary_result["data"]["Version"]
            jss_uploaded_package = jss_importer_summary_result["data"]["Package"]
            self.output(f"JSS address: {JSS_URL}")
            self.output(f"Title: {prod_name}")
            self.output(f"Policy: {jss_policy_name}")
            self.output(f"Version: {jss_policy_version}")
            self.output(f"Package Category: {category}")
            self.output(f"Policy Category: {policy_category}")
            self.output(f"Package: {jss_uploaded_package}")
            if jss_uploaded_package:
                slack_text = (
                    f"*New Item added to JSS:*\n"
                    "URL: {JSS_URL}\n"
                    "Title: *{prod_name}*\n"
                    "Version: *{jss_policy_version}*\n"
                    "Policy Name: *{jss_policy_name}*\n"
                    "Policy Category: *{policy_category}*\n"
                    "Package Category: *{category}*\n"
                    "Uploaded Package Name: *{jss_uploaded_package}*"
                )
            else:
                slack_text = (
                    f"*New Item added to JSS:*\n"
                    "URL: {JSS_URL}\n"
                    "Title: *{prod_name}*\n"
                    "Version: *{jss_policy_version}*\n"
                    "Policy Name: *{jss_policy_name}*\n"
                    "Policy Category: *{policy_category}*\n"
                    "Package Category: *{category}*\n"
                    "No new package uploaded"
                )

            slack_data = {"text": slack_text}

            response = requests.post(webhook_url, json=slack_data)
            if response.status_code != 200:
                raise ValueError(
                    f"Request to slack returned an error {response.status_code}, "
                    "the response is:\n{response.text}"
                )


if __name__ == "__main__":
    processor = Slacker()
    processor.execute_shell()
