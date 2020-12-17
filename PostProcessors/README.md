# Post-Processors

To use these processors, add the processor as so:

    com.github.grahampugh.recipes.postprocessors/NameOfProcessor

# LastRecipeRunResult

## Description

Writes useful results of a recipe to a JSON file, which can be used to run a different recipe based on those values.

## Input variables

- **RECIPE_CACHE_DIR:**

  - **required:** True (assumed from AutoPkg)
  - **description:** AutoPkg Cache directory.

- **output_file_path:**

  - **required:** False
  - **description:** Full path name to write JSON file of results to.
  - **default:** `RECIPE_CACHE_DIR`

- **output_file_name:**

  - **required:** False
  - **description:** Name of output file.
  - **default:** `latest_version.json`

- **url:**

  - **required:** False
  - **description:** The value of `url` from the recipe run.

- **pkg_path:**

  - **required:** False
  - **description:** The value of `pkg_path` from the recipe run.

- **pathname:**

  - **required:** False
  - **description:** The value of `pathname` from the recipe run.

- **version:**

  - **required:** False
  - **description:** The value of `version` from the recipe run.

- **PKG_CATEGORY:**

  - **required:** False
  - **description:** The value of `PKG_CATEGORY` from the recipe run.

- **SELFSERVICE_DESCRIPTION:**

  - **required:** False
  - **description:** The value of `SELFSERVICE_DESCRIPTION` from the recipe run.

## Output variables

- **url:**

  - **description:** The value of `url` from the recipe run.

- **pkg_path:**

  - **description:** The value of `pkg_path` from the recipe run.

- **pathname:**

  - **description:** The value of `pathname` from the recipe run.

- **version:**

  - **description:** The value of `version` from the recipe run.

- **PKG_CATEGORY:**

  - **description:** The value of `PKG_CATEGORY` from the recipe run.

- **SELFSERVICE_DESCRIPTION:**
  - **description:** The value of `SELFSERVICE_DESCRIPTION` from the recipe run.
