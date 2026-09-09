#!/usr/local/autopkg/python
#
# Copyright 2026 Graham Pugh
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
"""See docstring for FileRequired class"""

import os
import re

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["FileRequired"]


class FileRequired(Processor):
    """Raises a ProcessorError if the file named by a given input key is not
    supplied, does not exist on disk, or does not match an optional set of
    filename qualifications.

    This is a generalisation of the PackageRequired processor, which is
    hardcoded to the PKG key. Point key_name at any input variable that must
    hold a path to a file (or directory) the recipe cannot proceed without,
    e.g. a licence file, a branding image, or a configuration payload. Unlike
    a StopProcessingIf predicate, this raises (non-zero exit) both when the key
    is absent from the environment and when it is present but empty, so an
    operator who forgets to supply the value gets a clear failure rather than a
    silent no-op or an unsubstituted %VAR% reaching a later processor.

    Optionally qualify the supplied file further: allowed_extensions restricts
    the file suffix (e.g. an image or a .pkg), and filename_pattern requires
    the basename to match a regular expression. Either or both may be set; when
    both are set the file must satisfy both.
    """

    description = __doc__
    input_variables = {
        "key_name": {
            "required": True,
            "description": (
                "The name of the input variable that must contain a path to a "
                "required file or directory, e.g. 'WALLPAPER_FILE'."
            ),
        },
        "allowed_extensions": {
            "required": False,
            "description": (
                "Optional list of permitted file extensions (case-insensitive, "
                "with or without a leading dot), e.g. ['jpg', 'png'] or "
                "'jpg,png'. If set, the supplied file must end with one of "
                "these extensions."
            ),
        },
        "filename_pattern": {
            "required": False,
            "description": (
                "Optional regular expression that the supplied file's basename "
                "must match (via re.search), e.g. '^Sibelius_.*\\.dmg$'."
            ),
        },
    }
    output_variables = {}

    def _normalise_extensions(self, allowed_extensions):
        """Return a list of lower-case extensions without leading dots."""
        if isinstance(allowed_extensions, str):
            items = allowed_extensions.split(",")
        else:
            items = list(allowed_extensions)
        return [item.strip().lstrip(".").lower() for item in items if item.strip()]

    def main(self) -> None:
        """Main process."""
        key_name = self.env.get("key_name")
        value = self.env.get(key_name)

        if not value:
            raise ProcessorError(
                f"This recipe requires '{key_name}' to be supplied to autopkg "
                f'(e.g. via the "--key {key_name}=..." command-line switch or an '
                "override), but it was not provided."
            )

        if not os.path.exists(value):
            raise ProcessorError(
                f"Path supplied in '{key_name}' does not exist: {value}"
            )

        basename = os.path.basename(value.rstrip("/"))

        allowed_extensions = self.env.get("allowed_extensions")
        if allowed_extensions:
            extensions = self._normalise_extensions(allowed_extensions)
            if not any(basename.lower().endswith(f".{ext}") for ext in extensions):
                raise ProcessorError(
                    f"File supplied in '{key_name}' ({basename}) does not have "
                    f"an allowed extension ({', '.join(extensions)})."
                )

        filename_pattern = self.env.get("filename_pattern")
        if filename_pattern:
            if not re.search(filename_pattern, basename):
                raise ProcessorError(
                    f"File supplied in '{key_name}' ({basename}) does not match "
                    f"the required pattern: {filename_pattern}"
                )

        self.output(f"Required file '{key_name}' found: {value}")


if __name__ == "__main__":
    PROCESSOR = FileRequired()
    PROCESSOR.execute_shell()
