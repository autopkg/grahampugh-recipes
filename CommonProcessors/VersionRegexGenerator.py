#!/usr/local/autopkg/python

"""
VersionRegexGenerator processor for generating a regex which matches the
supplied version string or higher

by G Pugh

Acknowledgements:
This processor uses an amended version of "Match Version Number Or Higher.bash"
by William Smith, a shell script which determines a regex string of the current
or any possible higher version number from an inputted version string.
The amended version is included in this repo as
"match-version-number-or-higher.bash" and must be available to this processor.
See that file for full credits.
"""

# import variables go here. Do not import unused modules
import os.path
import subprocess
from pathlib import Path
from autopkglib import Processor, ProcessorError  # pylint: disable=import-error


class VersionRegexGenerator(Processor):
    """A processor for AutoPkg that will generating a regex which matches the supplied version
    string or higher."""

    input_variables = {
        "path_to_match_version_number_or_higher_script": {
            "required": False,
            "description": "A version string from which to perform the regex generation.",
            "default": "match-version-number-or-higher.bash",
        },
        "version": {
            "required": True,
            "description": (
                "A version string from which to perform the regex generation."
            ),
        },
    }

    output_variables = {
        "version_regex": {
            "description": "Regex which matches or exceeds the inputted version string.",
        },
        "version_regex_2": {
            "description": (
                "Regex which matches or exceeds the inputted version string - ",
                "second line for complex version strings.",
            ),
        },
        "version_regex_3": {
            "description": (
                "Regex which matches or exceeds the inputted version string - ",
                "third line for very complex version strings.",
            ),
        },
        "version_regex_4": {
            "description": (
                "Regex which matches or exceeds the inputted version string - ",
                "fourth line for extremely complex version strings.",
            ),
        },
        "version_regex_5": {
            "description": (
                "Regex which matches or exceeds the inputted version string - ",
                "fourth line for Microsoft-style version strings.",
            ),
        },
    }

    def get_path_to_file(self, filename):
        """AutoPkg is not very good at finding dependent files. This function will look
        inside the search directories for any supplied file"""
        # if the supplied file is not a path, use the override directory or
        # recipe dir if no override
        recipe_dir = self.env.get("RECIPE_DIR")
        filepath = os.path.join(recipe_dir, filename)
        if os.path.exists(filepath):
            self.output(f"File found at: {filepath}")
            return filepath

        # if not found, search RECIPE_SEARCH_DIRS to look for it
        search_dirs = self.env.get("RECIPE_SEARCH_DIRS")
        for d in search_dirs:
            for path in Path(d).rglob(filename):
                matched_filepath = str(path)
                break
        if matched_filepath:
            self.output(f"File found at: {matched_filepath}")
            return matched_filepath

    def main(self):
        """Do the main thing here"""
        version = self.env.get("version")
        if not version:
            raise ProcessorError("No version found!")

        path_to_match_version_number_or_higher_script = self.env.get(
            "path_to_match_version_number_or_higher_script"
        )
        # handle files with no path
        if "/" not in path_to_match_version_number_or_higher_script:
            path_to_match_version_number_or_higher_script = self.get_path_to_file(
                path_to_match_version_number_or_higher_script
            )

        cmd = [
            "/bin/bash",
            path_to_match_version_number_or_higher_script,
            "-q",
            "-j",
            version,
        ]
        regex_lines = subprocess.check_output(cmd).decode("ascii").splitlines()
        # complex version strings might output two or even three lines
        # so we have to account for this and have a second and third output variable
        self.env["version_regex"] = "^$"
        self.env["version_regex_2"] = "^$"
        self.env["version_regex_3"] = "^$"
        self.env["version_regex_4"] = "^$"
        self.env["version_regex_5"] = "^$"
        for i, regex_line in enumerate(regex_lines):
            self.output(f"Regex {i} for version string {version}: {regex_line}")
            if i == 0:
                self.env["version_regex"] = regex_line
            if i == 1:
                self.env["version_regex_2"] = regex_line
            if i == 2:
                self.env["version_regex_3"] = regex_line
            if i == 3:
                self.env["version_regex_4"] = regex_line
            if i == 4:
                self.env["version_regex_5"] = regex_line
            if i > 4:
                self.output(
                    "Warning: More than 5 regex lines generated, "
                    "only the first five will be used."
                )


if __name__ == "__main__":
    PROCESSOR = VersionRegexGenerator()
    PROCESSOR.execute_shell()
