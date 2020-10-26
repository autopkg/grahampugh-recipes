# Pre-Processors

To use these processors, add the processor as so:

    com.github.grahampugh.recipes.preprocessors/NameOfProcessor

# LastRecipeRunChecker

## Description

An AutoPkg pre-processor which reads the output from the `LastRecipeRunResult` post-processor from a different AutoPkg recipe, so that they can be used in the foillowing processes.

## Input variables

- **recipeoverride_identifier:**

  - **required:** True
  - **description:** The identifier of the recipe from which the information is required.

- **cache_dir:**

  - **required:** False
  - **description:** Path to the cache dir.
  - **default:** `~/Library/AutoPkg/Cache`

- **info_file:**

  - **required:** False
  - **description:** Name of input file.
  - **default:** `latest_version.json`

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
