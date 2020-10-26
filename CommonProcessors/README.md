# Common Processors

To use these processors, add the processor as so:

    com.github.grahampugh.recipes.commonprocessors/NameOfProcessor

## Index

- [ChangeModeOwner](#ChangeModeOwner)
- [ChoicesXMLGenerator](#ChoicesXMLGenerator)
- [JSSRecipeReceiptChecker](#JSSRecipeReceiptChecker)
- [LocalRepoUpdateChecker](#LocalRepoUpdateChecker)
- [SMBMounter](#SMBMounter)
- [SMBUnmounter](#SMBUnmounter)
- [StringReplacer](#StringReplacer)
- [SubDirectoryList](#SubDirectoryList)
- [VersionRegexGenerator](#VersionRegexGenerator)

# ChangeModeOwner

## Description

Similar to the `ChangeMode` Processor, but also has the ability to change the owner.

## Input variables

- **resource_path:**

  - **required:** True
  - **description:** Pathname of file/folder.

- **mode:**

  - **required:** False
  - **description:** chown(1) owner string to apply to file/folder, e.g. "root".

- **owner:**

  - **required:** False
  - **description:** chmod(1) mode string to apply to file/folder, e.g. "o-w", "755".

- **group:**
  - **required:** False
  - **description:** chown(1) group string to apply to file/folder, e.g. "wheel".

## Output variables

- None

# ChoicesXMLGenerator

## Description

Generates a `choices.xml` file for use with an installer. A postinstall script is required to run the installer with the `choices.xml.`

## Input variables

- **choices_pkg_path:**

  - **required:** True
  - **description:** Path to start looking for files.

- **desired_choices:**

  - **required:** False
  - **description:** A dictionary of choices.
  - **default:** `""`

- **choices_xml_dest:**
  - **required:** False
  - **description:** Path to save the choices.xml file. The processor will not do anything if none is provided.

## Output variables

- None

# JSSRecipeReceiptChecker

An AutoPkg processor which works out the latest receipt (by date) from a different AutoPkg recipe, and provides useful values from its contents, which can be used to run a different recipe based on those values.

## Description

## Input variables

- **name:**

  - **required:** True
  - **description:** This value should be the same as the `NAME` in the recipe from which we want to read the receipt. This is all we need to construct the override path.

- **cache_dir:**
  - **required:** False
  - **description:** Path to the cache dir.
  - **default:** `~/Library/AutoPkg/Cache`

## Output variables

- **pkg_path:**

  - **description:** Value of `pkg_path` obtained from the latest receipt.

- **version:**

  - **description:** Value of `version` obtained from the latest receipt.

- **CATEGORY:**

  - **description:** Value of `CATEGORY` obtained from the latest receipt.

- **SELF_SERVICE_DESCRIPTION:**
  - **description:** Value of `SELF_SERVICE_DESCRIPTION` obtained from the latest receipt.

# LocalRepoUpdateChecker

## Description

This processor assumes that a given folder contains sub-folders which are named after the version of their contents. The idea is that there is a single package, DMG or other installer inside the folder. The list of full paths to files in folders is generated using the `SubDirectoryList` processor, so this processor won't work unless `SubDirectoryList` is earlier in the list of procvesses.

If the subfolders have multiple contents, for example due to different language packs or some other variable, these should be filtered using the SubDirectoryList inputs, i.e. `LANGUAGE`, `LICENSE`, `LIMITATION`, `EXCEPTION`.

## Input variables

- **root_path:**

  - **required:** True
  - **description:** Repo path. Used here for comparisons.

- **found_filenames:**

  - **required:** True
  - **description:** Output of `found_filenames` from the `SubDirectoryList` processor.

- **RECIPE_CACHE_DIR:**
  - **required:** True (assumed from AutoPkg)
  - **description:** AutoPkg Cache directory.

## Output variables

- **version:**

  - **description:** The highest folder name according to LooseVersion logic.

- **latest_file:**

  - **description:** The filename of the highest version according to LooseVersion logic.

- **file_exists:**

  - **description:** Boolean to show whether the latest version is already present in the AutoPkg Cache.

- **cached_path:**
  - **description:** Path to the existing file in the AutoPkg Cache including filename.

# SMBMounter

## Description

Mounts an SMB directory. Expects a full SMB path as would be presented to `mount_smbfs`, because that's what it uses to mount. Valid examples:

    //server/share
    //server.com/share/subfolder/subsubfolder
    //user:password@server.com:123/share
    //DOMAIN;user:password@server/share

## Input variables

- **smb_path:**

  - **required:** True
  - **description:** SMB path including pre-slashes but excluding `smb:`.

- **mount_point:**
  - **required:** False
  - **description:** Output of `found_filenames` from the `SubDirectoryList` processor. Would require overriding if using the processor to mount more than one share.
  - **default:** `/tmp/tmp_autopkg_mount`

## Output variables

- None

# SMBUnmounter

## Description

Unmounts an SMB directory. Will fail if not following the `SMBMounter` processor.

## Input variables

- **mount_point:**

  - **required:** True
  - **description:** A mount point. Required, normally would be passed through from the `SMBMounter` processor.
  - **default:** `/tmp/tmp_autopkg_mount`

- `mount_point`: A mount point. Required, should be passed through from the `SMBMounter` processor.

## Output variables

- None

# StringReplacer

## Description

This processor replaces a string within a variable with another string, rather like using `sed`.
An example would be to remove a file suffix from a string.

## Input variables

- **input_string:**

  - **required:** True
  - **description:** A string to be processed, e.g. `filename.dmg`.

- **string_to_replace:**

  - **required:** True
  - **description:** The part of the `input_string` to be replaced, e.g. `.dmg`.

- **replacement_string:**

  - **required:** False
  - **description:** The string that should replace instances of `string_to_replace`. This can be left as an empty string if the purpose is to remove instances of `string_to_replace`.
  - **default:** `""`

## Output variables

- **output_string:**
  - **description:** The processed string.

# SubDirectoryList

## Description

This processor is used to generate a list of all files in folders in a path. That list is then processed by other processors such as `LocalRepoUpdateChecker`.

This processor is adapted from one written by Jesse Peterson. A newer version of that processor exists currently at [https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py](https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py).

## Input variables

- **root_path:**

  - **required:** True
  - **description:** String to append to each found item name in dir.
  - **default:** `,`

- **suffix_string:**

  - **required:** False
  - **description:** The string that should replace instances of `string_to_replace`. This can be left as an empty string if the purpose is to remove instances of `string_to_replace`.
  - **default:** `""`

- **max_depth:**

  - **required:** False
  - **description:** Maximum depth of folders to iterate through.
  - **default:** `2`

- **LANGUAGE:**

  - **required:** False
  - **description:** Language of the pkg or DMG containing PKG, one of `ML`, `DE`, `EN`. Basically acts as a string filter for the name of the DMG.
  - **default:** `""`

- **LICENSE:**

  - **required:** False
  - **description:** License of the pkg or DMG containing PKG, one of `Floating`, `Node`. Basically acts as a string filter for the name of the DMG.
  - **default:** `""`

- **EXCEPTION:**

  - **required:** False
  - **description:** A string variable to exclude from the search.
  - **default:** `""`

- **LIMITATION:**

  - **required:** False
  - **description:** A string variable to require in the search.
  - **default:** `""`

## Output variables

- **found_filenames:**

  - **description:** String containing a list of all files found relative to `root_path`, separated by `suffix_string`.

- **relative_root:**
  - **description:** Relative root path.

# VersionRegexGenerator

## Description

A processor for generating a regex which matches the inputted version string or any possible higher version. Useful for generating a string which can be added to the criterion of Jamf Pro Smart Groups so that only older versions of an application cause a computer to go in or out of scope.

This processor uses an amended version of `Match Version Number Or Higher.bash` by William Smith, a shell script which determines a regex string of the current or any possible higher version number from an inputted version string. the original version of this file was published as a Gist at [https://gist.github.com/2cf20236e665fcd7ec41311d50c89c0e](https://gist.github.com/2cf20236e665fcd7ec41311d50c89c0e). The amendments were necessary to provide a "quiet" output mode which prints only the version regex string(s) without any additional outputs.

Note that for very complicated version strings, the regex may exceed 255 characters. Jamf Pro cannot accept strings longer than 255 characters, so this processor will create multiple regex strings that can be added as additional criteria in a smart group. Your subsequent processor design will have to accommodate this, so beware when using a version string that is on the cusp of generating a 255 character regex string, in case a change means that the first regex string no longer accounts for all possibilities.

## Input variables

- **version:**

  - **required:** True
  - **description:** A version string with which to generate a regex that matches the version or higher.
  - **default:** `2`

- **path_to_match_version_number_or_higher_script:**

  - **required:** False
  - **description:** The full path to the file `match-version-number-or-higher.bash`. The processor will look for the file in your `RECIPE_DIR` (RecipeOverrides folder) and in `RECIPE_SEARCH_DIRS`. The file is also provided in the same folder as the `VersionRegexGenerator` processor.

## Output variables

- **version_regex:**

  - **description:** The version regex (maximum length 255 characters).

- **version_regex_2:**

  - **description:** An additional version regex for very complicated version strings, since Jamf cannot manage strings of more than 255 characters. Or `^$` if not required.

- **version_regex_3:**
  - **description:** An additional version regex for extremely complicated version strings, since Jamf cannot manage strings of more than 255 characters. Or `^$` if not required.
