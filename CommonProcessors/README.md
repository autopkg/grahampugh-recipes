# Common Processors

To use these processors, add the processor as so:

    com.github.grahampugh.recipes.commonprocessors/NameOfProcessor

# SubDirectoryList

This processor is adapted from one written by Jesse Peterson. A newer version of that processor exists currently at [https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py](https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py).

It is used to generate a list of all files in folders in a path. That list is then processed by other processors such as `LocalRepoUpdateChecker` (see below).

### Inputs

* `root_path`: Path to start looking for files. Required.
* `suffix_string`: String to append to each found item name in dir. Defaults to `,`. Optional.
* `max_depth`: Maximum depth of folders to iterate through. Default: `2`.
* `LANGUAGE`: Language of the pkg or DMG containing PKG, one of `ML`, `DE`, `EN`. Basically acts as a string filter for the name of the DMG. Optional.
* `LICENSE`: License of the pkg or DMG containing PKG, one of `Floating`, `Node`. Basically acts as a string filter for the name of the DMG. Optional.
* `EXCEPTION`: A string variable to exclude from the search. Optional.
* `LIMITATION`: A string variable to require in the search. Optional.

### Outputs

* `found_filenames`: String containing a list of all files found relative to `root_path`, separated by  `suffix_string`.
* `relative_root`: Relative root path.


# LocalRepoUpdateChecker

This processor assumes that a given folder contains sub-folders which are named after the version of their contents. The idea is that there is a single package, DMG or other installer inside the folder. The list of full paths to files in folders is generated using the SubDirectoryList processor. If the subfolders have multiple contents, for example due to different language packs or some other variable, these should be filtered using the SubDirectoryList inputs, i.e. LANGUAGE, LICENSE, LIMITATION, EXCEPTION.

### Inputs

* `root_path`: Repo path. Used here for comparisons. Required.
* `found_filenames`: Output of SubDirectoryList `found_filenames`. Required.
* `RECIPE_CACHE_DIR`: AutoPkg Cache directory. Required.

### Outputs

* `version`: The highest folder name according to LooseVersion logic.
* `latest_file`: The filename of the highest version according to LooseVersion logic.
* `file_exists`: Boolean to show whether the latest version is already present in the AutoPkg Cache
* `cached_path`: Path to the existing file in the AutoPkg Cache including filename


# JSSRecipeReceiptChecker

An AutoPkg processor which works out the latest receipt (by date) from a different AutoPkg recipe, and provides useful values from its contents, which can be used to run a different recipe based on those values.

### Inputs

* `name`: This value should be the same as the NAME in the recipe from which we want to read the receipt. This is all we need to construct the override path. Required.
* `cache_dir`: Path to the cache dir. Defaults to `~/Library/AutoPkg/Cache`. Optional.

### Outputs

* `pkg_path`: Value obtained from the latest receipt.
* `version`: Value obtained from the latest receipt.
* `CATEGORY`: Value obtained from the latest receipt.
* `SELF_SERVICE_DESCRIPTION`: Value obtained from the latest receipt.


# ChangeModeOwner

Similar to the `ChangeMode` Processor, but also has the ability to change the owner.

### Inputs

* `resource_path`: Pathname of file/folder. Required.
* `mode`: chmod(1) mode string to apply to file/folder, e.g. "o-w", "755". Optional.
* `owner`: chown(1) owner string to apply to file/folder, e.g. "root". Optional.
* `group`: chown(1) group string to apply to file/folder, e.g. "wheel". Optional.

### Outputs

None


# ChoicesXMLGenerator

Generates a `choices.xml` file for use with an installer. A postinstall script is required to run the installer with the `choices.xml.`

### Inputs

* `choices_pkg_path`: Path to start looking for files. Required.
* `desired_choices`: A dictionary of choices. Defaults to empty. Optional.
* `choices_xml_dest`: Path to save the choices.xml file. Optional, but the processor will not do anything if none is provided.

### Outputs

None
