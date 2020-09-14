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

## ChangeModeOwner

Similar to the `ChangeMode` Processor, but also has the ability to change the owner.

### Inputs

- `resource_path`: Pathname of file/folder. Required.
- `mode`: chmod(1) mode string to apply to file/folder, e.g. "o-w", "755". Optional.
- `owner`: chown(1) owner string to apply to file/folder, e.g. "root". Optional.
- `group`: chown(1) group string to apply to file/folder, e.g. "wheel". Optional.

### Outputs

- None

## ChoicesXMLGenerator

Generates a `choices.xml` file for use with an installer. A postinstall script is required to run the installer with the `choices.xml.`

### Inputs

- `choices_pkg_path`: Path to start looking for files. Required.
- `desired_choices`: A dictionary of choices. Defaults to empty. Optional.
- `choices_xml_dest`: Path to save the choices.xml file. Optional, but the processor will not do anything if none is provided.

### Outputs

- None

## JSSRecipeReceiptChecker

An AutoPkg processor which works out the latest receipt (by date) from a different AutoPkg recipe, and provides useful values from its contents, which can be used to run a different recipe based on those values.

### Inputs

- `name`: This value should be the same as the NAME in the recipe from which we want to read the receipt. This is all we need to construct the override path. Required.
- `cache_dir`: Path to the cache dir. Defaults to `~/Library/AutoPkg/Cache`. Optional.

### Outputs

- `pkg_path`: Value obtained from the latest receipt.
- `version`: Value obtained from the latest receipt.
- `CATEGORY`: Value obtained from the latest receipt.
- `SELF_SERVICE_DESCRIPTION`: Value obtained from the latest receipt.

## LocalRepoUpdateChecker

This processor assumes that a given folder contains sub-folders which are named after the version of their contents. The idea is that there is a single package, DMG or other installer inside the folder. The list of full paths to files in folders is generated using the SubDirectoryList processor. If the subfolders have multiple contents, for example due to different language packs or some other variable, these should be filtered using the SubDirectoryList inputs, i.e. LANGUAGE, LICENSE, LIMITATION, EXCEPTION.

### Inputs

- `root_path`: Repo path. Used here for comparisons. Required.
- `found_filenames`: Output of SubDirectoryList `found_filenames`. Required.
- `RECIPE_CACHE_DIR`: AutoPkg Cache directory. Required.

### Outputs

- `version`: The highest folder name according to LooseVersion logic.
- `latest_file`: The filename of the highest version according to LooseVersion logic.
- `file_exists`: Boolean to show whether the latest version is already present in the AutoPkg Cache
- `cached_path`: Path to the existing file in the AutoPkg Cache including filename

## SMBMounter

Mounts an SMB directory. Expects a full SMB path as would be presented to `mount_smbfs`, because that's what it uses to mount. Valid examples:

    //server/share
    //server.com/share/subfolder/subsubfolder
    //user:password@server.com:123/share
    //DOMAIN;user:password@server/share

### Inputs

- `smb_path`: SMB path including pre-slashes but excluding `smb:`. Required.
- `mount_point`: A mount point. Optional, defaults to `/tmp/tmp_autopkg_mount`. Would require overriding if using the processor to mount more than one share.

### Outputs

- None

## SMBUnmounter

Unmounts an SMB directory. Will fail if not following the `SMBMounter` processor.

### Inputs

- `mount_point`: A mount point. Required, should be passed through from the `SMBMounter` processor.

### Outputs

- None

## StringReplacer

This processor replaces a string within a variable with another string, rather like using `sed`.
An example would be to remove a file suffix from a string.

### Inputs

- `input_string`: A string to be processed, e.g. `filename.dmg`. Required.
- `string_to_replace`: The part of the `input_string` to be replaced, e.g. `.dmg`. Required.
- `replacement_string`: The string that should replace instances of `string_to_replace`. Optional - this can be an empty string if the purpose is to remove instances of `string_to_replace`.

### Outputs

- `output_string`: The processed string.

## SubDirectoryList

This processor is adapted from one written by Jesse Peterson. A newer version of that processor exists currently at [https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py](https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py).

It is used to generate a list of all files in folders in a path. That list is then processed by other processors such as `LocalRepoUpdateChecker` (see below).

### Inputs

- `root_path`: Path to start looking for files. Required.
- `suffix_string`: String to append to each found item name in dir. Defaults to `,`. Optional.
- `max_depth`: Maximum depth of folders to iterate through. Default: `2`.
- `LANGUAGE`: Language of the pkg or DMG containing PKG, one of `ML`, `DE`, `EN`. Basically acts as a string filter for the name of the DMG. Optional.
- `LICENSE`: License of the pkg or DMG containing PKG, one of `Floating`, `Node`. Basically acts as a string filter for the name of the DMG. Optional.
- `EXCEPTION`: A string variable to exclude from the search. Optional.
- `LIMITATION`: A string variable to require in the search. Optional.

### Outputs

- `found_filenames`: String containing a list of all files found relative to `root_path`, separated by `suffix_string`.
- `relative_root`: Relative root path.

## VersionRegexGenerator

A processor for generating a regex which matches the inputted version string or any possible higher version. Useful for generating a string which can be added to the criterion of Jamf Pro Smart Groups so that only older versions of an application cause a computer to go in or out of scope.

This processor uses an amended version of `Match Version Number Or Higher.bash` by William Smith, a shell script which determines a regex string of the current or any possible higher version number from an inputted version string. the original version of this file was published as a Gist at [https://gist.github.com/2cf20236e665fcd7ec41311d50c89c0e](https://gist.github.com/2cf20236e665fcd7ec41311d50c89c0e). The amendments were necessary to provide a "quiet" output mode which prints only the version regex string(s) without any additional outputs.

Note that for very complicated version strings, the regex may exceed 255 characters. Jamf Pro cannot accept strings longer than 255 characters, so this processor will create multiple regex strings that can be added as additional criteria in a smart group. Your subsequent processor design will have to accommodate this, so beware when using a version string that is on the cusp of generating a 255 character regex string, in case a change means that the first regex string no longer accounts for all possibilities.

### Inputs

- `version`: A version string with which to generate a regex that matches the version or higher. Required.
- `path_to_match_version_number_or_higher_script`: The full path to the file `match-version-number-or-higher.bash`. Optional. The processor will look for the file in your `RECIPE_DIR` (RecipeOverrides folder) and in `RECIPE_SEARCH_DIRS`. The file is also provided in the same folder as the `VersionRegexGenerator` processor.

### Outputs

- `version_regex`: The version regex.
- `version_regex_2`: An additional version regex for very complicated version strings, since Jamf cannot manage strings of more than 255 characters.
- `version_regex_3`: An additional version regex for extremely complicated version strings, since Jamf cannot manage strings of more than 255 characters.
