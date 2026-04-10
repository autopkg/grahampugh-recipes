# JamfCLIRunner

An AutoPkg processor that runs commands against the [jamf-cli](https://concepts.jamf.com/jamf-cli/) binary, enabling AutoPkg recipes to create, update, query, and manage objects in Jamf Pro and Jamf Protect.

## Prerequisites

- **jamf-cli** must be installed and available in the system `PATH` (or set `jamf_cli_binary` to its absolute path).
- At least one profile must be configured via `jamf-cli config` identifying a Jamf Pro or Jamf Protect instance.

## Processor reference

### Command structure

The processor constructs and runs:

```sh
jamf-cli --no-color --no-input <type> <endpoint> [<action>] [<identifier>] [flags]
```

`--no-color` and `--no-input` are always set. All other flags are derived from input variables and are silently omitted when not set.

### Referencing the processor in a recipe

```yaml
- Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
```

### Required input variables

| Key | Description |
|-----|-------------|
| `type` | Top-level product namespace: `pro`, `protect`, or `multi`. The `config` and `completion` types are blocked. |
| `endpoint` | API endpoint or Power Command, e.g. `categories`, `computers`, `icons`, `plans`. |

### Common optional input variables

| Key | CLI flag | Description |
|-----|----------|-------------|
| `action` | positional | Action to perform: `get`, `list`, `apply`, `delete`, `upload`, etc. |
| `identifier` | positional | Resource ID or name, placed after the action by default. |
| `identifier_before_action` | — | If `true`, the identifier is placed before the action (required for the `device` Power Command). |
| `profile` | `--profile` | jamf-cli profile name identifying the target instance. |
| `confirm` | `--yes` | If truthy, passes `--yes` to skip confirmation prompts. |
| `confirm_destructive` | `--confirm-destructive` | Required for bulk-delete operations. |
| `dry_run` | `--dry-run` | Preview changes without applying them. |
| `all` | `--all` | Fetch all paginated results (valid on `list` and `history` actions). |
| `verbose` | `--verbose` | Show HTTP debug info on stderr. Recommended when using `object_updated`. |
| `output` | `-o` | Output format: `table`, `json`, `csv`, `yaml`, or `plain`. |
| `filter` | `--filter` | Filter query, e.g. `osVersion>=15`. Only supported on `computers-inventories`. |
| `sort` | `--sort` | Sort criteria, e.g. `name:asc`. |
| `out_file` | `--out-file` | Write output to a file path. |
| `from_file` | `--from-file` | Path to a JSON or YAML payload file. Supports `%KEY%` substitution. |
| `body_file` | `--body-file` | Alternative body file flag for endpoints that use `--body-file`. Supports `%KEY%` substitution. |
| `data` | `--from-file` | Inline dictionary payload written to a temporary JSON file. Ignored if `from_file` is set. |
| `file` | `--file` | Path to a binary file to upload (packages, scripts, icons). When set, `from_file`/`data` processing is skipped entirely. |
| `serial` | `--serial` | Target device by serial number. |
| `device_id` | `--id` | Target device by numeric ID. |
| `device_name` | `--name` | Target device or resource by name. |
| `output_vars` | — | Dictionary mapping new env key names to response key names (see [output_vars](#output_vars)). |

### Output variables

| Key | Description |
|-----|-------------|
| `jamf_cli_output` | Raw stdout from the command. |
| `jamf_cli_exit_code` | Integer exit code. |
| `jamf_cli_response` | Parsed JSON response dict (when the output is a JSON object). |
| `object_updated` | `True` if the object was created or updated; `False` if it already existed and was intentionally not replaced. See [object_updated](#object_updated). |
| `jamfclirunner_summary_result` | AutoPkg summary shown at the end of the run. |
| *(response keys)* | Each top-level key from a JSON object response is also exported individually, e.g. `%id%`, `%name%`. |

---

## Examples

### 1. List all computers

```yaml
- Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
  Arguments:
    type: pro
    endpoint: computers
    action: list
    profile: "%PROFILE%"
    all: true
```

Equivalent command: `jamf-cli --no-color --no-input pro computers list --all --profile my-instance`

---

### 2. Get a computer by serial number

```yaml
- Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
  Arguments:
    type: pro
    endpoint: computers-inventories
    action: get
    profile: "%PROFILE%"
    serial: "%SERIAL%"
```

The response keys (`id`, `name`, `udid`, etc.) are exported to the environment automatically and can be referenced as `%id%`, `%name%` in subsequent processors.

---

### 3. Inline payload with `data`

Use `data` when the JSON body is simple enough to write directly in the recipe. Values from `%VARIABLE%` substitution are coerced to the appropriate JSON type (`"10"` → `10`, `"true"` → `true`).

```yaml
Input:
  CATEGORY: Utilities
  PRIORITY: "9"

Process:
  - Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
    Arguments:
      type: pro
      endpoint: categories
      action: apply
      profile: "%PROFILE%"
      confirm: "true"
      data:
        name: "%CATEGORY%"
        priority: "%PRIORITY%"
```

Equivalent command: `jamf-cli --no-color --no-input pro categories apply --yes --profile my-instance --from-file /tmp/tmpXXXX.json`

Where the temporary file contains:

```json
{
  "name": "Utilities",
  "priority": 9
}
```

The temporary file is created before the command runs and deleted immediately afterwards, even if the command fails.

---

### 4. Template file with `from_file` and variable substitution

For more complex payloads, place a JSON or YAML template file alongside the recipe. Any `%KEY%` tokens in the file are substituted from the AutoPkg environment before the file is passed to jamf-cli.

**`JamfPro-Package.json`** (in the same folder as the recipe):

```json
{
  "packageName": "%pkg_name%",
  "notes": "%pkg_notes%",
  "priority": "%pkg_priority%"
}
```

**Recipe:**

```yaml
Input:
  pkg_notes: Uploaded by AutoPkg
  pkg_priority: "10"

Process:
  - Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
    Arguments:
      type: pro
      endpoint: packages
      action: apply
      profile: "%PROFILE%"
      confirm: "true"
      from_file: JamfPro-Package.json
```

`pkg_name` is derived automatically from `pkg_path` if it is set by an earlier processor (e.g. a download or packaging step).

The processor searches for the template file in this order:

1. RecipeOverrides directories (recursive)
2. The same directory as the recipe
3. Sibling directories of the recipe directory
4. Recipe search directories (repo roots)
5. The parent recipe's repo (when running as an override)

---

### 5. File upload with `--file`

Commands that perform binary uploads (packages, scripts, icons, config profiles) use `--file` rather than `--from-file`. Setting the `file` key automatically disables `data`/`from_file` processing so no spurious `--from-file` argument is added.

```yaml
- Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
  Arguments:
    type: pro
    endpoint: icons
    action: upload
    profile: "%PROFILE%"
    file: "%app_icon_path%"
    output_vars:
      app_icon_id: id
      app_icon_url: url
```

---

### 6. Multi-processor workflow with `output_vars`

When a recipe runs JamfCLIRunner more than once, each invocation exports response keys like `id` and `name` to the environment, overwriting values from the previous run. Use `output_vars` to rename exported keys to stable, unique names before the next processor runs.

`output_vars` is a dictionary where:

- **key** = the new environment variable name to set
- **value** = the source key name from the JSON response

```yaml
Process:
  # Step 1 — ensure the package category exists, capture its id
  - Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
    Arguments:
      type: pro
      endpoint: categories
      action: apply
      profile: "%PROFILE%"
      confirm: "true"
      data:
        name: Utilities
        priority: 9
      output_vars:
        pkg_category_id: id
        pkg_category_name: name

  # Step 2 — ensure the policy category exists, capture its id under a different name
  - Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
    Arguments:
      type: pro
      endpoint: categories
      action: apply
      profile: "%PROFILE%"
      confirm: "true"
      data:
        name: Testing
        priority: 9
      output_vars:
        policy_category_id: id
        policy_category_name: name

  # Step 3 — create the package record, referencing both captured IDs via a template
  - Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
    Arguments:
      type: pro
      endpoint: packages
      action: apply
      profile: "%PROFILE%"
      confirm: "true"
      from_file: JamfPro-Package.json
```

After step 1, `%pkg_category_id%` and `%pkg_category_name%` are set.
After step 2, `%policy_category_id%` and `%policy_category_name%` are set, and `%id%`/`%name%` now reflect the policy category — but the package category values are safe in their renamed keys.

The template file `JamfPro-Package.json` can then reference any of these:

```json
{
  "packageName": "%pkg_name%",
  "categoryId": "%pkg_category_id%"
}
```

---

### 7. `object_updated` and `StopProcessingIf`

`apply` without `confirm: "true"` will not replace an object that already exists. jamf-cli exits with code 1 in that case, but the HTTP response is 200 — the object was found, just not modified. The processor treats this as a soft success rather than an error, and sets `object_updated` to `False`.

This is useful in package-deployment recipes: if the package record already exists at the correct version there is no need to re-upload the binary or update the policy.

```yaml
Input:
  REPLACE_PKG: "false"   # set to "true" to force replacement

Process:
  - Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
    Arguments:
      type: pro
      endpoint: packages
      action: apply
      profile: "%PROFILE%"
      confirm: "%REPLACE_PKG%"
      verbose: "true"       # required for HTTP status detection
      from_file: JamfPro-Package.json

  # Stop here if nothing changed — no need to re-upload the pkg or update the policy
  - Processor: StopProcessingIf
    Arguments:
      predicate: "object_updated == False"

  # Only reached when the package record was newly created or updated
  - Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
    Arguments:
      type: pro
      endpoint: packages
      action: upload
      profile: "%PROFILE%"
      file: "%pkg_path%"
```

> **Note:** `verbose: "true"` must be set on the processor call that may exit with code 1. The HTTP status detection relies on jamf-cli's `--verbose` stderr output. Without it, any non-zero exit is treated as an error.

---

### 8. Jamf Protect

The same processor handles Jamf Protect by changing `type` to `protect`.

```yaml
- Processor: com.github.grahampugh.recipes.JamfCLIRunner/JamfCLIRunner
  Arguments:
    type: protect
    endpoint: plans
    action: list
    profile: "%PROTECT_PROFILE%"
    all: true
    output: json
    out_file: "%RECIPE_CACHE_DIR%/plans.json"
```

---

## YAML key naming caution

PyYAML (used by AutoPkg) follows YAML 1.1, which treats a wide set of unquoted words as booleans — including `yes`, `no`, `true`, `false`, `on`, `off`, and their all-caps variants (`YES`, `NO`, `TRUE`, `FALSE`, `ON`, `OFF`). If any of these appear as unquoted keys in a recipe's `Input` or `Arguments` section they will be parsed as Python booleans, causing AutoPkg to fail with a `TypeError` when serialising the run results.

**Avoid** using these words as input variable names. If you must, quote them:

```yaml
# Problematic — YES is a YAML 1.1 boolean key
Input:
  YES: "false"      # key parsed as True (bool), not "YES" (string)

# Safe
Input:
  CONFIRM: "false"  # not a YAML boolean
  "YES": "false"    # quoted — forces string key
```

The processor uses `confirm` (not `yes`) as its input key for the `--yes` flag precisely to avoid this issue.
