#!/usr/local/autopkg/python
"""AutoPkg processor for dissecting monolithic profiles into discrete preference files."""

import os
import plistlib
from typing import Any, Dict

from autopkglib import ProcessorError, URLGetter  # pylint: disable=import-error

try:
    import yaml
except ImportError as err:
    raise ProcessorError(
        "pyyaml is required to use the MonolithicProfileConverter processor"
    ) from err

__all__ = ["MonolithicProfileDissector"]


class MonolithicProfileDissector(URLGetter):
    """Dissect a .mobileconfig profile into per-domain preference files."""

    description = __doc__
    input_variables = {
        "mobileconfig_path": {
            "required": True,
            "description": "Path to the source mobile configuration profile.",
        },
        "output_dir": {
            "required": False,
            "description": (
                "Directory where the generated PLIST files should be written. "
                "Defaults to the directory containing the source profile."
            ),
            "default": "",
        },
    }
    output_variables = {
        "converted_profile_paths": {
            "description": "List of generated per-domain preference files.",
        }
    }

    BASE_URL = "https://raw.githubusercontent.com/apple/device-management/release/mdm/profiles/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

    def fetch_schema(self, domain: str) -> Dict[str, Any]:
        """Download and cache the schema for a preference domain."""
        if domain in self._schema_cache:
            return self._schema_cache[domain]

        schema_url = f"{self.BASE_URL}{domain}.yaml"
        try:
            schema_bytes = self.download(schema_url)
            schema_text = schema_bytes.decode("utf-8")
            schema_data = yaml.safe_load(schema_text) or {}
            self._schema_cache[domain] = schema_data
            self.output(f"Fetched schema for {domain}", verbose_level=2)
        except Exception as err:  # pylint: disable=broad-except
            self.output(
                f"WARNING: Could not retrieve schema for {domain}: {err}",
                verbose_level=1,
            )
            schema_data = {}
            self._schema_cache[domain] = schema_data

        return schema_data

    def get_default_values(self, domain: str) -> Dict[str, Any]:
        """Return default key/value pairs for a domain from the schema."""
        schema = self.fetch_schema(domain)
        defaults: Dict[str, Any] = {}
        for key_info in schema.get("payloadkeys", []) or []:
            key_name = key_info.get("key")
            default_value = key_info.get("default")
            if key_name is not None and default_value is not None:
                defaults[key_name] = default_value
        return defaults

    def read_mobileconfig(self, file_path: str) -> Dict[str, Any]:
        """Load the mobile configuration profile."""
        try:
            with open(file_path, "rb") as mobileconfig:
                return plistlib.load(mobileconfig)
        except Exception as err:  # pylint: disable=broad-except
            raise ProcessorError(f"Could not read mobile config file: {err}") from err

    @staticmethod
    def extract_payloads_by_domain(
        config_data: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """Extract payload settings grouped by payload type."""
        domain_payloads: Dict[str, Dict[str, Any]] = {}
        payload_content = config_data.get("PayloadContent", [])

        for payload in payload_content:
            payload_type = payload.get("PayloadType")
            if not payload_type or payload_type == "Configuration":
                continue

            excluded_keys = {
                "PayloadDescription",
                "PayloadDisplayName",
                "PayloadEnabled",
                "PayloadIdentifier",
                "PayloadOrganization",
                "PayloadType",
                "PayloadUUID",
                "PayloadVersion",
            }
            preference_keys: Dict[str, Any] = {}
            for key, value in payload.items():
                if key not in excluded_keys:
                    preference_keys[key] = value

            if not preference_keys:
                continue
            if payload_type in domain_payloads:
                domain_payloads[payload_type].update(preference_keys)
            else:
                domain_payloads[payload_type] = preference_keys

        return domain_payloads

    def filter_non_defaults(
        self, domain: str, payload_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return only values that differ from documented defaults."""
        defaults = self.get_default_values(domain)
        non_defaults: Dict[str, Any] = {}

        for key, value in payload_data.items():
            default_value = defaults.get(key)
            if default_value is None:
                self.output(f"  Skipping {key}: no documented default", verbose_level=2)
                continue
            if value != default_value:
                non_defaults[key] = value
                self.output(
                    f"  {key}: {value} (default: {default_value})", verbose_level=2
                )
            else:
                self.output(
                    f"  {key}: matches default ({default_value})", verbose_level=3
                )
        return non_defaults

    @staticmethod
    def create_plist_file(domain: str, data: Dict[str, Any], output_dir: str) -> str:
        """Write a PLIST file for a specific domain."""
        filename = f"{domain}.plist"
        file_path = os.path.join(output_dir, filename)
        try:
            with open(file_path, "wb") as plist_file:
                plistlib.dump(data, plist_file)
        except Exception as err:  # pylint: disable=broad-except
            raise ProcessorError(
                f"Could not write PLIST file {filename}: {err}"
            ) from err
        return file_path

    def main(self):
        """Processor entry point."""
        mobileconfig_path = self.env.get("mobileconfig_path")
        if not mobileconfig_path:
            raise ProcessorError("The 'mobileconfig_path' input variable is required.")
        if not os.path.exists(mobileconfig_path):
            raise ProcessorError(
                f"Mobile configuration file not found: {mobileconfig_path}"
            )

        output_dir = self.env.get("output_dir") or ""
        if output_dir:
            output_dir = os.path.expanduser(output_dir)
        else:
            output_dir = os.path.dirname(os.path.abspath(mobileconfig_path))
        os.makedirs(output_dir, exist_ok=True)

        self.output(f"Analyzing mobile configuration: {mobileconfig_path}")
        config_data = self.read_mobileconfig(mobileconfig_path)
        domain_payloads = self.extract_payloads_by_domain(config_data)
        if not domain_payloads:
            raise ProcessorError("No preference domains found in the configuration.")
        self.output(f"Found {len(domain_payloads)} preference domains", verbose_level=1)

        created_files = []
        for domain, payload_data in domain_payloads.items():
            self.output(f"Processing domain: {domain}")
            non_defaults = self.filter_non_defaults(domain, payload_data)
            if not non_defaults:
                self.output(
                    "  All values match defaults, no file created", verbose_level=2
                )
                continue
            file_path = self.create_plist_file(domain, non_defaults, output_dir)
            created_files.append(file_path)
            self.output(f"  Created: {file_path}")

        self.env["converted_profile_paths"] = created_files
        self.output(f"Generated {len(created_files)} preference file(s).")


if __name__ == "__main__":
    PROCESSOR = MonolithicProfileDissector()
    PROCESSOR.execute_shell()
