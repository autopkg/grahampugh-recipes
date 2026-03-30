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

"""
ModelIdentifierRegexGenerator processor for generating a regex that matches
supported Mac Model Identifiers for a given macOS version.

Fetches an EveryMac compatibility page, extracts the supported Model IDs from
the HTML table, and produces a concise regex string suitable for use in Jamf Pro
Smart Groups or other matching contexts.
"""

import re

from autopkglib import URLGetter, ProcessorError  # pylint: disable=import-error

__all__ = ["ModelIdentifierRegexGenerator"]

# Known legacy Model ID family prefixes (order matters: longer prefixes first
# so that e.g. "MacBookPro" is matched before "MacBook" and "Mac")
LEGACY_FAMILIES = [
    "iMacPro",
    "iMac",
    "MacBookPro",
    "MacBookAir",
    "MacBook",
    "Macmini",
    "MacPro",
]

# The order in which families appear in the final regex
FAMILY_ORDER = [
    "Mac",
    "MacBookAir",
    "MacBook",
    "Macmini",
    "MacPro",
    "iMacPro",
    "iMac",
    "MacBookPro",
]


class ModelIdentifierRegexGenerator(URLGetter):
    """A processor for AutoPkg that fetches an EveryMac macOS compatibility page
    and generates a regex matching all supported Mac Model Identifiers."""

    input_variables = {
        "compatibility_url": {
            "required": True,
            "description": (
                "URL of an EveryMac macOS compatibility page, e.g. "
                "https://everymac.com/mac-answers/macos-26-tahoe-faq/"
                "macos-tahoe-macos-26-compatbility-list-system-requirements.html"
            ),
        },
    }

    output_variables = {
        "model_identifier_regex": {
            "description": (
                "A regex string matching all supported Model Identifiers "
                "extracted from the compatibility page, plus VirtualMac."
            ),
        },
    }

    description = __doc__

    def extract_supported_section(self, html):
        """Extract the HTML of the first table after 'Supported Systems'
        and before 'Unsupported Systems'."""
        # Find the supported systems heading
        supported_match = re.search(r"Supported\s+Systems\s*</", html, re.IGNORECASE)
        if not supported_match:
            raise ProcessorError(
                "Could not find 'Supported Systems' section in the page"
            )

        # From that point, find the first <table> and its closing </table>
        after_heading = html[supported_match.end() :]
        table_start = re.search(r"<table\b", after_heading, re.IGNORECASE)
        if not table_start:
            raise ProcessorError(
                "Could not find a table after 'Supported Systems' heading"
            )

        table_end = re.search(
            r"</table>", after_heading[table_start.start() :], re.IGNORECASE
        )
        if not table_end:
            raise ProcessorError("Could not find end of supported systems table")

        section = after_heading[
            table_start.start() : table_start.start() + table_end.end()
        ]
        return section

    def extract_model_ids(self, html_section):
        """Extract unique Model IDs from an HTML section.
        Returns a sorted list of unique (family, major, minor) tuples."""
        model_ids = set()

        # Match legacy-style IDs: iMac20,1  MacBookPro16,2  etc.
        for family in LEGACY_FAMILIES:
            pattern = rf"(?<!\w){re.escape(family)}(\d+),(\d+)"
            for match in re.finditer(pattern, html_section):
                major = int(match.group(1))
                minor = int(match.group(2))
                model_ids.add((family, major, minor))

        # Match new-style "Mac" IDs (e.g. Mac13,1  Mac14,7)
        # Use negative lookbehind to avoid matching MacPro, Macmini, MacBook*
        for match in re.finditer(r"(?<![a-zA-Z])Mac(\d+),(\d+)", html_section):
            major = int(match.group(1))
            minor = int(match.group(2))
            model_ids.add(("Mac", major, minor))

        if not model_ids:
            raise ProcessorError("No Model IDs found in the supported section")

        return sorted(
            model_ids,
            key=lambda x: (
                FAMILY_ORDER.index(x[0]) if x[0] in FAMILY_ORDER else 999,
                x[1],
                x[2],
            ),
        )

    def group_by_family(self, model_ids):
        """Group model IDs by family. Returns dict of family -> sorted list of
        unique major numbers."""
        families = {}
        for family, major, _minor in model_ids:
            families.setdefault(family, set()).add(major)
        return {f: sorted(majors) for f, majors in families.items()}

    def optimise_major_range(self, majors):
        """Generate an optimised regex fragment for a list of major version
        numbers, with future-proofing.

        Strategy:
        - Single-digit numbers that are the only entry: just the digit
        - All two-digit in the same tens group: tens_digit[min_ones-9]
          (future-proofed to 9)
        - Mix of single and two-digit: alternation with future-proofing
        - Multiple tens groups: alternation of each group
        """
        if not majors:
            return ""

        min_major = min(majors)
        max_major = max(majors)

        # All single-digit
        if max_major <= 9:
            if min_major == max_major:
                return str(min_major)
            return f"[{min_major}-9]"

        # All two-digit, same tens group
        tens_min = min_major // 10
        tens_max = max_major // 10

        if tens_min == tens_max and min_major >= 10:
            ones_min = min_major % 10
            return f"{tens_min}[{ones_min}-9]"

        # Two-digit spanning multiple tens groups - future-proof
        # e.g. majors [13,14,15,16] -> 1[3-9] (extend to 9)
        if min_major >= 10:
            ones_min = min_major % 10
            if tens_min == tens_max:
                return f"{tens_min}[{ones_min}-9]"
            # Spans tens boundaries - build alternation
            parts = []
            # First partial tens group
            parts.append(f"{tens_min}[{ones_min}-9]")
            # Full middle tens groups
            for t in range(tens_min + 1, tens_max):
                parts.append(f"{t}[0-9]")
            # Last partial tens group (future-proofed to 9)
            if tens_max > tens_min:
                parts.append(f"{tens_max}[0-9]")
            if len(parts) == 1:
                return parts[0]
            return f"({'|'.join(parts)})"

        # Mix of single-digit and two-digit
        single = [m for m in majors if m <= 9]
        multi = [m for m in majors if m >= 10]
        parts = []
        if single:
            if len(single) == 1:
                parts.append(str(single[0]))
            else:
                parts.append(f"[{min(single)}-9]")
        if multi:
            parts.append(self.optimise_major_range(multi))
        if len(parts) == 1:
            return parts[0]
        return f"({'|'.join(parts)})"

    def build_family_regex(self, family, majors):
        """Build a regex fragment for one Model ID family."""
        major_regex = self.optimise_major_range(majors)

        if family == "Mac":
            # Generic Mac prefix with anchor
            return f"^Mac{major_regex}," + r"\b[0-9]{1,2}\b"

        if family == "iMac":
            # iMac uses \d for minor (following Sequoia convention)
            return f"iMac({major_regex})," + r"\d+"

        # All other legacy families
        return f"{family}{major_regex}," + r"\b[0-9]{1,2}\b"

    def build_full_regex(self, family_majors):
        """Build the complete regex from per-family data."""
        parts = []

        for family in FAMILY_ORDER:
            if family in family_majors:
                parts.append(self.build_family_regex(family, family_majors[family]))

        # Add any families not in FAMILY_ORDER (shouldn't happen, but safe)
        for family in sorted(family_majors.keys()):
            if family not in FAMILY_ORDER:
                parts.append(self.build_family_regex(family, family_majors[family]))

        # Always add VirtualMac
        parts.append("VirtualMac")

        return "(" + "|".join(parts) + ")"

    def validate_regex(self, regex_str, model_ids):
        """Test the generated regex against all extracted Model IDs.
        Returns list of IDs that failed to match."""
        compiled = re.compile(regex_str)
        failures = []
        for family, major, minor in model_ids:
            model_id = f"{family}{major},{minor}"
            if not compiled.search(model_id):
                failures.append(model_id)
        # Also test VirtualMac
        if not compiled.search("VirtualMac2,1"):
            failures.append("VirtualMac2,1")
        return failures

    def main(self):
        """Do the main thing here"""
        compatibility_url = self.env.get("compatibility_url")
        if not compatibility_url:
            raise ProcessorError("No compatibility_url provided!")

        self.output(f"Fetching: {compatibility_url}")

        # Fetch the page using URLGetter's download method (curl)
        # A browser-like User-Agent is required or everymac.com returns 403
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko)"
            ),
        }
        html = self.download(compatibility_url, headers=headers, text=True)

        if not html:
            raise ProcessorError(f"Failed to download content from {compatibility_url}")

        self.output(f"Downloaded {len(html)} bytes", verbose_level=2)

        # Extract the supported systems section
        section = self.extract_supported_section(html)
        self.output(
            f"Extracted supported section ({len(section)} chars)", verbose_level=2
        )

        # Extract Model IDs
        model_ids = self.extract_model_ids(section)
        unique_ids = sorted({f"{f}{maj},{mi}" for f, maj, mi in model_ids})
        self.output(f"Found {len(unique_ids)} unique Model IDs:", verbose_level=2)
        for mid in unique_ids:
            self.output(f"  {mid}", verbose_level=2)

        # Group by family
        family_majors = self.group_by_family(model_ids)
        for family in FAMILY_ORDER:
            if family in family_majors:
                self.output(
                    f"  {family}: majors {family_majors[family]}", verbose_level=2
                )

        # Build the regex
        regex_str = self.build_full_regex(family_majors)

        # Validate
        failures = self.validate_regex(regex_str, model_ids)
        if failures:
            self.output(f"WARNING: regex does not match these Model IDs: {failures}")

        self.output(f"Generated regex: {regex_str}")
        self.env["model_identifier_regex"] = regex_str


if __name__ == "__main__":
    PROCESSOR = ModelIdentifierRegexGenerator()
    PROCESSOR.execute_shell()
