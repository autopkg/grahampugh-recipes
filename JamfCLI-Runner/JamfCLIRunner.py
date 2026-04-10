#!/usr/local/autopkg/python
# pylint: disable=invalid-name

"""
Copyright 2026 Graham Pugh

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

NOTES:
This processor provides an interface to the jamf-cli binary.

Command structure:
    jamf-cli <type> <endpoint> [<action>] [<identifier>] [flags]

  type       - Top-level product namespace: pro, protect, multi.
               The 'config' and 'completion' types are blocked.
  endpoint   - API endpoint (e.g. 'computers', 'computer-groups', 'policies')
               or a Power Command (e.g. 'group-tools', 'device').
  action     - Action to perform on the endpoint (e.g. 'get', 'list',
               'create', 'update', 'delete'). Not required for Power Commands
               that act directly on an identifier.
  identifier - Optional resource identifier (ID or name). Appended after the
               action for standard CRUD endpoints, e.g.:
                 jamf-cli pro computers get 123
               For the 'device' Power Command, where the identifier comes
               before the action (e.g. jamf-cli pro device 123 erase), set
               identifier_before_action to True.

Flags are derived from the optional input variables listed below. Flags whose
values are empty, False, or not set are omitted from the command. Input keys
use underscores in place of hyphens, e.g. 'out_file' maps to '--out-file'.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# Matches ANSI/VT100 escape sequences (colours, cursor movement, etc.)
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[@-_]")

# Matches HTTP response status lines in jamf-cli --verbose stderr output,
# e.g. "<-- 200 200 OK" or "<-- 409 409 Conflict"
_HTTP_RESPONSE_RE = re.compile(r"<--\s+(\d{3})")

from autopkglib import Processor, ProcessorError  # pylint: disable=import-error

__all__ = ["JamfCLIRunner"]

# Types that must never be passed to jamf-cli from this processor
BLOCKED_TYPES = {"config", "completion"}

# Boolean flags: input key -> CLI flag
BOOL_FLAGS = {
    "all": "--all",
    "scaffold": "--scaffold",
    "dry_run": "--dry-run",
    "confirm": "--yes",
    "confirm_destructive": "--confirm-destructive",
    "quiet": "--quiet",
    "wide": "--wide",
    "verbose": "--verbose",
}

# Value flags: input key -> CLI flag
VALUE_FLAGS = {
    "profile": "--profile",
    "serial": "--serial",
    "device_id": "--id",
    "device_name": "--name",
    "group": "--group",
    "device_ids": "--ids",
    "section": "--section",
    "filter": "--filter",
    "limit": "--limit",
    "page": "--page",
    "page_size": "--page-size",
    "sort": "--sort",
    "output": "-o",
    "field": "--field",
    "out_file": "--out-file",
    "from_file": "--from-file",
    "body_file": "--body-file",
    "save_to": "--save-to",
    "file": "--file",
    "tenant_id": "--tenant-id",
    "token_file": "--token-file",
    "jamf_url": "--url",
}


class JamfCLIRunner(Processor):
    """A processor for AutoPkg that interfaces with the jamf-cli binary.

    Runs a jamf-cli command built from the provided input variables. The
    'config' and 'completion' top-level types are blocked. Optional flags are
    included only when their values are set; unset or falsy flags are silently
    omitted, so the same recipe key set can be reused across endpoints and
    actions without causing unknown-flag errors.
    """

    description = __doc__

    input_variables = {
        "pkg_path": {
            "required": False,
            "description": (
                "Full path to a package file, typically set by an earlier AutoPkg "
                "processor. If present and 'pkg_name' is not already set, the "
                "processor derives 'pkg_name' as the basename of this path before "
                "template substitution runs, making %pkg_name% available in templates."
            ),
        },
        "pkg_name": {
            "required": False,
            "description": (
                "Basename of the package file (e.g. 'MyApp-1.0.pkg'). Set explicitly "
                "or derived automatically from 'pkg_path' if that key is present."
            ),
        },
        "jamf_cli_binary": {
            "required": False,
            "description": (
                "Path to the jamf-cli binary. Defaults to 'jamf-cli' in the system PATH."
            ),
            "default": "jamf-cli",
        },
        "type": {
            "required": True,
            "description": (
                "Top-level jamf-cli product namespace, e.g. 'pro', 'protect', 'multi'. "
                "The 'config' and 'completion' types are not permitted."
            ),
        },
        "endpoint": {
            "required": True,
            "description": (
                "API endpoint or Power Command, e.g. 'computers', 'computer-groups', "
                "'policies', 'device', 'group-tools'."
            ),
        },
        "action": {
            "required": False,
            "description": (
                "Action to perform, e.g. 'get', 'list', 'create', 'update', 'delete'. "
                "Not required for Power Commands that act directly on an identifier."
            ),
        },
        "identifier": {
            "required": False,
            "description": (
                "Resource identifier (ID or name) passed as a positional argument. "
                "By default it is placed after the action "
                "(e.g. 'jamf-cli pro computers get 123'). "
                "Set identifier_before_action to True for endpoints such as 'device' "
                "where the identifier precedes the action "
                "(e.g. 'jamf-cli pro device 123 erase')."
            ),
        },
        "identifier_before_action": {
            "required": False,
            "description": (
                "If True, the identifier is placed before the action rather than after. "
                "Required for the 'device' Power Command and similar endpoints. "
                "Defaults to False."
            ),
        },
        "profile": {
            "required": False,
            "description": (
                "The jamf-cli profile name identifying which Jamf Pro or Jamf Protect "
                "instance to target, as configured via 'jamf-cli config'. "
                "Maps to --profile <name>."
            ),
        },
        # --- Boolean flags ---
        "all": {
            "required": False,
            "description": "If True, passes --all to fetch all paginated results.",
        },
        "scaffold": {
            "required": False,
            "description": "If True, passes --scaffold to print a JSON template.",
        },
        "dry_run": {
            "required": False,
            "description": "If True, passes --dry-run to preview changes without applying them.",
        },
        "confirm": {
            "required": False,
            "description": "If True, passes --yes to jamf-cli to skip confirmation prompts.",
        },
        "confirm_destructive": {
            "required": False,
            "description": (
                "If True, passes --confirm-destructive, required for bulk delete operations."
            ),
        },
        "quiet": {
            "required": False,
            "description": "If True, passes --quiet to suppress non-error output.",
        },
        "wide": {
            "required": False,
            "description": "If True, passes --wide to show all columns in table output.",
        },
        "verbose": {
            "required": False,
            "description": "If True, passes --verbose to show HTTP debug info on stderr.",
        },
        # --- Device targeting flags ---
        "serial": {
            "required": False,
            "description": "Device serial number. Maps to --serial <serial>.",
        },
        "device_id": {
            "required": False,
            "description": "Device numeric ID. Maps to --id <id>.",
        },
        "device_name": {
            "required": False,
            "description": "Device or resource name. Maps to --name <name>.",
        },
        "group": {
            "required": False,
            "description": "Target all members of a named device group. Maps to --group <name>.",
        },
        "device_ids": {
            "required": False,
            "description": "Comma-separated list of IDs for bulk operations. Maps to --ids <ids>.",
        },
        # --- Value flags ---
        "section": {
            "required": False,
            "description": (
                "Inventory section to return, e.g. 'GENERAL', 'HARDWARE'. "
                "Maps to --section <section>."
            ),
        },
        "save_to": {
            "required": False,
            "description": "File path to save downloaded content to. Maps to --save-to <path>.",
        },
        "file": {
            "required": False,
            "description": "Path to a file to upload. Maps to --file <path>.",
        },
        "filter": {
            "required": False,
            "description": (
                "Filter query string, e.g. 'osVersion>=15'. Maps to --filter <value>."
            ),
        },
        "limit": {
            "required": False,
            "description": "Maximum total results to return (0 = unlimited). Maps to --limit <n>.",
        },
        "page": {
            "required": False,
            "description": "Page number to fetch. Maps to --page <n>.",
        },
        "page_size": {
            "required": False,
            "description": "Number of items per page (default 100). Maps to --page-size <n>.",
        },
        "sort": {
            "required": False,
            "description": (
                "Sorting criteria in the format 'property:asc/desc'. "
                "Multiple criteria separated by comma, e.g. 'date:desc,name:asc'. "
                "Maps to --sort <value>."
            ),
        },
        "output": {
            "required": False,
            "description": (
                "Output format: table, json, csv, yaml, or plain. Maps to -o <format>."
            ),
        },
        "field": {
            "required": False,
            "description": "Extract a single named field from the response. Maps to --field <name>.",
        },
        "out_file": {
            "required": False,
            "description": "Write output to this file path. Maps to --out-file <path>.",
        },
        "from_file": {
            "required": False,
            "description": (
                "Read input payload from this JSON or YAML file path. Maps to --from-file <path>. "
                "If 'data' is also provided, 'from_file' takes precedence."
            ),
        },
        "data": {
            "required": False,
            "description": (
                "A dictionary of key-value pairs to pass as the --from-file payload. "
                "Use this instead of 'from_file' when the content can be expressed inline "
                'in the recipe, e.g. \'{"name": "%CATEGORY%", "priority": 10}\'. '
                "The dictionary is serialised to a temporary JSON file which is automatically "
                "cleaned up after the command runs. Ignored if 'from_file' is also set."
            ),
        },
        "tenant_id": {
            "required": False,
            "description": (
                "Jamf Pro tenant ID for platform gateway authentication. "
                "Maps to --tenant-id <id> (or set JAMF_TENANT_ID env var)."
            ),
        },
        "token_file": {
            "required": False,
            "description": "Path to a file containing an API token. Maps to --token-file <path>.",
        },
        "jamf_url": {
            "required": False,
            "description": (
                "Jamf Pro/Protect server URL. Maps to --url <url> "
                "(or set JAMF_URL env var)."
            ),
        },
        "output_vars": {
            "required": False,
            "description": (
                "Optional dictionary mapping new environment key names to source key names "
                "from the JSON response. Use this to rename exported response keys so that "
                "multiple processors can run without their output keys overwriting each other. "
                "Keys in this dict are the desired environment variable names; values are the "
                "source key names as exported from the JSON response. "
                'Example: {"pkg_category_id": "id", "pkg_category_name": "name"}.'
            ),
        },
    }

    output_variables = {
        "jamf_cli_output": {
            "description": "The stdout output from the jamf-cli command.",
        },
        "jamf_cli_exit_code": {
            "description": "The integer exit code returned by jamf-cli.",
        },
        "jamfclirunner_summary_result": {
            "description": "Summary of the jamf-cli command that was executed.",
        },
        "jamf_cli_response": {
            "description": (
                "When the output is a JSON object (e.g. from get, create, apply, update), "
                "the parsed dict is stored here. Each top-level key is also exported "
                "individually to the environment so subsequent processors can reference "
                "them directly, e.g. '%id%' or '%name%'."
            ),
        },
        "object_updated": {
            "description": (
                "True if the object was created or updated (exit code 0). "
                "False if jamf-cli exited with code 1 but all observed HTTP responses "
                "were 2xx, which indicates the object already existed and was intentionally "
                "not replaced (e.g. 'apply' without '--yes'). "
                "Use with StopProcessingIf to halt subsequent processors when no change "
                "was made: predicate 'object_updated == False'."
            ),
        },
    }

    # Keys whose values are file paths and should be resolved via get_path_to_file
    FILE_KEYS = {"from_file", "body_file", "file"}

    def _coerce_data_value(self, value):
        """Coerce a value from the 'data' dict to an appropriate JSON type.

        AutoPkg variable substitution always produces strings, so "%PRIORITY%"
        arrives as "10" and "%YES%" arrives as "true". This converts those
        strings to int/float/bool where unambiguous, leaving everything else
        as a plain string.
        """
        if not isinstance(value, str):
            return value  # already int, bool, float, list, dict, etc.
        stripped = value.strip()
        if stripped.lower() == "true":
            return True
        if stripped.lower() == "false":
            return False
        try:
            return int(stripped)
        except ValueError:
            pass
        try:
            return float(stripped)
        except ValueError:
            pass
        return value

    def _coerce_data_dict(self, d):
        """Recursively coerce all values in a dict via _coerce_data_value."""
        return {
            k: (
                self._coerce_data_dict(v)
                if isinstance(v, dict)
                else self._coerce_data_value(v)
            )
            for k, v in d.items()
        }

    def substitute_assignable_keys(self, text):
        """Replace all %KEY% tokens in text with values from the AutoPkg environment.

        Uses up to five passes so that substitutions whose values themselves
        contain %KEY% tokens are fully resolved. Raises ProcessorError if any
        token remains unresolvable after all passes.
        """
        for _ in range(5):
            found_keys = re.findall(r"%(\w+)%", text)
            if not found_keys:
                break
            for key in found_keys:
                value = self.env.get(key)
                if value is not None:
                    self.output(
                        f"Substituting %{key}% with {str(value)!r}",
                        verbose_level=2,
                    )
                    text = text.replace(f"%{key}%", str(value))
                else:
                    raise ProcessorError(f"Unsubstitutable key in template: '%{key}%'")
        return text

    def _substitute_file(self, file_path, tmp_files):
        """Read a template file, substitute %KEY% tokens, and write the result
        to a new temporary file. Returns the path to the substituted file and
        appends it to tmp_files for later cleanup."""
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                original = fh.read()
        except OSError as e:
            raise ProcessorError(
                f"Could not read template file {file_path}: {e}"
            ) from e

        substituted = self.substitute_assignable_keys(original)

        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=os.path.splitext(file_path)[1] or ".json",
            delete=False,
            encoding="utf-8",
        )
        tmp.write(substituted)
        tmp.close()
        tmp_files.append(tmp.name)
        self.output(f"Wrote substituted template to: {tmp.name}")
        return tmp.name

    def get_path_to_file(self, filename):
        """Find a file without requiring a full path. Searches in order:
        1. RecipeOverrides directories (recursive)
        2. Same directory as the recipe
        3. Sibling directories of the recipe directory
        4. Recipe search directories (repo roots) that match the recipe's location
        5. Parent recipe's repo if running as an override
        """
        recipe_dir = self.env.get("RECIPE_DIR")
        recipe_dir_path = Path(os.path.expanduser(recipe_dir))
        matched_override_dir = ""
        matched_filepath = ""

        # 1. RecipeOverrides directories
        self.output(f"Looking for {filename} in RECIPE_OVERRIDE_DIRS", verbose_level=3)
        if self.env.get("RECIPE_OVERRIDE_DIRS"):
            for d in self.env["RECIPE_OVERRIDE_DIRS"]:
                override_dir_path = Path(os.path.expanduser(d))
                if (
                    override_dir_path == recipe_dir_path
                    or override_dir_path in recipe_dir_path.parents
                ):
                    self.output(f"Matching dir: {override_dir_path}", verbose_level=3)
                    matched_override_dir = override_dir_path
                for path in Path(os.path.expanduser(d)).rglob(filename):
                    matched_filepath = str(path)
                    break
            if matched_filepath:
                self.output(f"File found at: {matched_filepath}")
                return matched_filepath
        else:
            self.output("No RECIPE_OVERRIDE_DIRS defined", verbose_level=3)

        # 2. Same directory as the recipe
        self.output(
            f"Looking for {filename} in {recipe_dir} or its siblings", verbose_level=3
        )
        filepath = os.path.join(recipe_dir, filename)
        if os.path.exists(filepath):
            self.output(f"File found at: {filepath}")
            return filepath

        # 3. Sibling directories
        self.output(
            f"Checking sibling directories of {recipe_dir_path}", verbose_level=3
        )
        for sibling in recipe_dir_path.parent.iterdir():
            if sibling.is_dir() and sibling != recipe_dir_path:
                self.output(
                    f"Looking for {filename} in sibling directory: {sibling}",
                    verbose_level=3,
                )
                filepath = os.path.join(sibling, filename)
                if os.path.exists(filepath):
                    self.output(f"File found at: {filepath}")
                    return filepath

        # 4. Recipe search directories (repo roots)
        if self.env.get("RECIPE_SEARCH_DIRS"):
            matched_filepath = ""
            for d in self.env["RECIPE_SEARCH_DIRS"]:
                search_dir_path = Path(os.path.expanduser(d))
                self.output(f"Recipe directory: {recipe_dir_path}", verbose_level=3)
                self.output(
                    f"Looking for {filename} in {search_dir_path}", verbose_level=3
                )
                if (
                    search_dir_path == recipe_dir_path
                    or search_dir_path.parent == recipe_dir_path.parent
                    or search_dir_path == recipe_dir_path.parent
                    or search_dir_path in recipe_dir_path.parent.parents
                ):
                    self.output(f"Matching dir: {search_dir_path}", verbose_level=3)
                    for path in Path(os.path.expanduser(d)).rglob(filename):
                        matched_filepath = str(path)
                        break
                if matched_filepath:
                    self.output(f"File found at: {matched_filepath}")
                    return matched_filepath
            self.output(
                f"File {filename} not found in any RECIPE_SEARCH_DIRS", verbose_level=3
            )

        # 5. Parent recipe's repo if running as an override
        if matched_override_dir:
            if self.env.get("PARENT_RECIPES"):
                self.output(
                    f"Looking for {filename} in parent recipe's repo", verbose_level=3
                )
                matched_filepath = ""
                parent = self.env["PARENT_RECIPES"][0]
                self.output(f"Parent Recipe: {parent}", verbose_level=2)
                parent_dir = os.path.dirname(parent)
                parent_dir_path = Path(os.path.expanduser(parent_dir))
                for d in self.env.get("RECIPE_SEARCH_DIRS", []):
                    search_dir_path = Path(os.path.expanduser(d))
                    if (
                        search_dir_path == parent_dir_path
                        or search_dir_path in parent_dir_path.parents
                    ):
                        self.output(f"Matching dir: {search_dir_path}", verbose_level=3)
                        for path in Path(os.path.expanduser(d)).rglob(filename):
                            matched_filepath = str(path)
                            break
                    if matched_filepath:
                        self.output(f"File found at: {matched_filepath}")
                        return matched_filepath

        raise ProcessorError(f"File '{filename}' not found")

    def _is_truthy(self, value):
        """Return True if value represents a truthy boolean input."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() not in ("", "false", "0", "no", "none")

    def _build_command(self, binary, cli_type, endpoint, action, identifier, id_before):
        """Assemble the positional part of the jamf-cli command."""
        # --no-color and --no-input are always set: plist serialisation requires
        # clean text, and AutoPkg recipes must never block on interactive prompts.
        cmd = [binary, "--no-color", "--no-input", cli_type, endpoint]

        if identifier and id_before:
            cmd.append(identifier)

        if action:
            cmd.append(action)

        if identifier and not id_before:
            cmd.append(identifier)

        return cmd

    def _append_flags(self, cmd):
        """Append optional flags to cmd based on set input variables."""
        for key, flag in BOOL_FLAGS.items():
            if self._is_truthy(self.env.get(key)):
                cmd.append(flag)

        for key, flag in VALUE_FLAGS.items():
            value = self.env.get(key)
            if value is not None and str(value).strip():
                cmd.extend([flag, str(value).strip()])

        return cmd

    def main(self):
        """Build and execute the jamf-cli command."""
        binary = self.env.get("jamf_cli_binary") or "jamf-cli"
        cli_type = self.env.get("type", "").strip()
        endpoint = self.env.get("endpoint", "").strip()
        action = (self.env.get("action") or "").strip() or None
        identifier = (self.env.get("identifier") or "").strip() or None
        id_before = self._is_truthy(self.env.get("identifier_before_action"))

        # Validate binary
        if not shutil.which(binary):
            raise ProcessorError(f"jamf-cli binary not found: {binary}")

        # Validate type
        if not cli_type:
            raise ProcessorError("The 'type' input variable is required.")
        if cli_type.lower() in BLOCKED_TYPES:
            raise ProcessorError(
                f"The '{cli_type}' type is not permitted. "
                f"Blocked types: {', '.join(sorted(BLOCKED_TYPES))}."
            )

        # Validate endpoint
        if not endpoint:
            raise ProcessorError("The 'endpoint' input variable is required.")

        # Track all temporary files created during this run for cleanup.
        tmp_files = []
        # Also record which env keys we set from temp files so they can be
        # cleared after the run, preventing stale paths leaking to the next
        # processor invocation in the same recipe.
        tmp_env_keys = []

        # Commands that accept --file (binary/multipart uploads) never also
        # accept --from-file (JSON/YAML body). Skip all body-file processing
        # when --file is in use so those commands are not given a spurious
        # --from-file argument.
        using_file_upload = bool((self.env.get("file") or "").strip())

        if not using_file_upload:
            # If 'data' is provided and 'from_file' is not, serialise 'data' to a
            # temporary JSON file and use that as the --from-file value.
            data_value = self.env.get("data")
            from_file_value = (self.env.get("from_file") or "").strip()
            if data_value is not None and not from_file_value:
                if not isinstance(data_value, dict):
                    raise ProcessorError(
                        f"'data' must be a dictionary, got {type(data_value).__name__}"
                    )
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                json.dump(self._coerce_data_dict(data_value), tmp, indent=2)
                tmp.close()
                tmp_files.append(tmp.name)
                tmp_env_keys.append("from_file")
                self.env["from_file"] = tmp.name
                self.output(f"Wrote 'data' to temporary file: {tmp.name}")

        # Resolve file-type inputs to absolute paths
        for key in self.FILE_KEYS:
            value = (self.env.get(key) or "").strip()
            if value and not os.path.isabs(value):
                self.env[key] = self.get_path_to_file(value)

        # If pkg_path is in the environment and pkg_name is not already set,
        # derive pkg_name from the basename so templates can reference %pkg_name%.
        if self.env.get("pkg_path") and not self.env.get("pkg_name"):
            self.env["pkg_name"] = os.path.basename(self.env["pkg_path"])
            self.output(
                f"Derived pkg_name: {self.env['pkg_name']!r} from pkg_path",
                verbose_level=2,
            )

        if not using_file_upload:
            # Substitute %KEY% tokens in from_file and body_file template content.
            # 'file' is left as-is because it is a binary (package, script, etc.)
            # that should not be text-processed.
            for key in ("from_file", "body_file"):
                value = (self.env.get(key) or "").strip()
                if value and os.path.isfile(value):
                    substituted_path = self._substitute_file(value, tmp_files)
                    if key not in tmp_env_keys:
                        tmp_env_keys.append(key)
                    self.env[key] = substituted_path

        # Build command
        cmd = self._build_command(
            binary, cli_type, endpoint, action, identifier, id_before
        )
        cmd = self._append_flags(cmd)

        self.output(f"Running: {' '.join(cmd)}")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = proc.communicate()
            exit_code = proc.returncode
        finally:
            for path in tmp_files:
                if os.path.exists(path):
                    os.unlink(path)
            # Clear env keys that pointed at temp files so that a subsequent
            # processor in the same recipe does not inherit stale paths.
            for key in tmp_env_keys:
                self.env[key] = ""

        stdout_str = _ANSI_ESCAPE.sub(
            "", stdout.decode("utf-8", errors="replace")
        ).strip()
        stderr_str = _ANSI_ESCAPE.sub(
            "", stderr.decode("utf-8", errors="replace")
        ).strip()

        if stdout_str:
            self.output(f"Output:\n{stdout_str}")
        if stderr_str:
            self.output(f"Stderr:\n{stderr_str}", verbose_level=2)

        self.env["jamf_cli_output"] = stdout_str
        self.env["jamf_cli_exit_code"] = exit_code

        # Determine whether the operation made a change and whether a non-zero
        # exit code represents a real failure or a deliberate no-op.
        #
        # jamf-cli exits 1 when an object already exists and --yes was not
        # supplied (e.g. `apply` without `--confirm`).  In that case all HTTP
        # activity visible in --verbose stderr is successful (2xx), so we treat
        # the run as a soft success: object_updated = False, no exception raised.
        #
        # Any other non-zero exit (4xx/5xx responses, no HTTP activity, etc.)
        # is still surfaced as a ProcessorError.
        object_updated = True
        if exit_code != 0:
            http_codes = [int(c) for c in _HTTP_RESPONSE_RE.findall(stderr_str)]
            if http_codes and all(200 <= c < 300 for c in http_codes):
                object_updated = False
                self.output(
                    f"jamf-cli exited with code {exit_code} but all HTTP responses "
                    f"were successful {http_codes} — object already exists, no change made."
                )
            else:
                raise ProcessorError(
                    f"jamf-cli exited with code {exit_code}."
                    + (f" Stderr: {stderr_str}" if stderr_str else "")
                )

        # Parse JSON output and export top-level keys so subsequent processors
        # can reference them directly, e.g. %id% or %name%.
        # Only done when the object was actually created/updated; when
        # object_updated is False the stdout contains a jamf-cli error envelope
        # (with keys like "error", "message") that should not pollute the env.
        # Arrays (list output) are also skipped as they have no useful key mapping.
        if object_updated and stdout_str:
            try:
                parsed = json.loads(stdout_str)
                if isinstance(parsed, dict):
                    self.env["jamf_cli_response"] = parsed
                    for key, value in parsed.items():
                        self.env[key] = value
                        self.output(
                            f"Exported response key: {key} = {value!r}",
                            verbose_level=2,
                        )
            except (json.JSONDecodeError, ValueError):
                pass

        # Apply output_vars remapping: for each new_key -> source_key entry,
        # copy the value of source_key in the env to new_key.
        output_vars = self.env.get("output_vars")
        if output_vars:
            if not isinstance(output_vars, dict):
                raise ProcessorError(
                    f"'output_vars' must be a dictionary, got {type(output_vars).__name__}"
                )
            for new_key, source_key in output_vars.items():
                if source_key in self.env:
                    self.env[new_key] = self.env[source_key]
                    self.output(
                        f"Mapped response key: {source_key!r} -> {new_key!r} = {self.env[new_key]!r}",
                        verbose_level=2,
                    )
                else:
                    self.output(
                        f"output_vars: source key {source_key!r} not found in environment, skipping",
                        verbose_level=2,
                    )

        self.env["object_updated"] = object_updated

        self.env["jamfclirunner_summary_result"] = {
            "summary_text": "The following jamf-cli command was run:",
            "report_fields": ["command", "exit_code", "object_updated"],
            "data": {
                "command": " ".join(cmd),
                "exit_code": str(exit_code),
                "object_updated": str(object_updated),
            },
        }


if __name__ == "__main__":
    PROCESSOR = JamfCLIRunner()
    PROCESSOR.execute_shell()
