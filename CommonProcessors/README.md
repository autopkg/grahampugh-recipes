# Common Processors

To use these processors, add the processor as so:

    com.github.grahampugh.recipes.commonprocessors/NameOfProcessor

## Index

- [ChangeModeOwner](#changemodeowner)
- [ChoicesXMLGenerator](#choicesxmlgenerator)
- [IconGenerator](#icongenerator)
- [JSSRecipeReceiptChecker](#jssrecipereceiptchecker)
- [NSURLDownloader](#NSURLDownloader)
- [PkgInfoReader](#pkginforeader)
- [SMBMounter](#smbmounter)
- [SMBUnmounter](#smbunmounter)
- [StringReplacer](#stringreplacer)
- [VersionRegexGenerator](#versionregexgenerator)

# ChangeModeOwner

## Description

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

## Description

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

# IconGenerator

## Description

An AutoPkg processor based on [AppIconExtractor](https://github.com/autopkg/haircut-recipes/blob/master/Processors/AppIconExtractor.py) with the alternative option to supply an icon rather than point to an app. See [Haircut's Blog Post](https://macblog.org/autopkg-icons/) about AppIconEtractor.

## Input variables

- **source_icon:**

  - **required:** False
  - **description:** The input path of the icon. This can be supplied as an alternative to the app path. If just an icon name is supplied without a path, the repo that the recipe is in, or the folder that it's in, will be searched to look for the icon.

- **source_app:**

  - **required:** False
  - **description:** Path to the .app from which to extract an icon. Can point to a path inside a .dmg which will be mounted. This path may also contain basic globbing characters such as the wildcard '*', but only the first result will be returned.

- **icon_output_path:**

  - **required:** False
  - **description:** The output path to write the .png icon. If not set, defaults to %RECIPE_CACHE_DIR%/%NAME%.png
  - **default:** `""`

- **composite_install_path:**
  - **required:** False
  - **description:** The output path to write the composited 'install' icon .png, where `composite_install_template` is superimposed on top of the app icon. If not set, no 'install' composite icon will be created.

- **composite_install_template:**
  - **required:** False
  - **description:** Path to a template icon to composite on top of the app's icon to create an 'install' icon version. If not set, a default template icon is used.

- **composite_update_path:**
  - **required:** False
  - **description:** The output path to write the composited 'update' icon .png, where `composite_update_template` is superimposed on top of the app icon. If not set, no 'update' composite icon will be created.

- **composite_update_template:**
  - **required:** False
  - **description:** Path to a template icon to composite on top of the app's icon to create an 'update' icon version. If not set, a default template icon is used.

- **composite_uninstall_path:**
  - **required:** False
  - **description:** The output path to write the composited 'uninstall' icon .png, where `composite_uninstall_template` is superimposed on top of the app icon. If not set, no 'uninstall' composite icon will be created.

- **composite_uninstall_template:**
  - **required:** False
  - **description:** Path to a template icon to composite on top of the app's icon to create an 'uninstall' icon version. If not set, a default template icon is used.

- **composite_position:**
  - **required:** False
  - **description:** The anchor position at which to add the composited template icons. One of: `br` (bottom right), `bl` (bottom left), `ur` (upper right), or ul (upper left). Defaults to `br`.

- **composite_padding:**
  - **required:** False
  - **description:** The number of both horizontal and vertical pixels to add as padding from the edge of the app icon when compositing a template icon on top. Defaults to `10`.

## Output variables

- **app_icon_path:**
  - **description:** The path on disk to the plain, uncomposited app icon.

- **install_icon_path:**
  - **description:** The path on disk to the 'install' composited icon variation, if requested.

- **app_icon_path:**
  - **description:** The path on disk to the 'update' composited icon variation, if requested.

- **app_icon_path:**
  - **description:** The path on disk to the 'uninstall' composited icon variation, if requested.

# JSSRecipeReceiptChecker

An AutoPkg processor which works out the latest receipt (by date) from a different AutoPkg recipe, and provides useful values from its contents, which can be used to run a different recipe based on those values.

## Description

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

# PkgInfoReader

## Description

This processor looks for information in packages with the primary objective of
    obtaining the package version. If there are multiple packages within the package,
    the highest version number found will be returned in the 'version' variable.

This code is adapted largely from Munki's [pkgutils.py](https://github.com/munki/munki/blob/main/code/client/munkilib/pkgutils.py), written by Greg Neagle.

## Input variables

- **source_pkg:**
  - **description:** The path of the package to interrogate.

## Output Variables

- **cataloginfo:**
  - **description:** A dictionary of information from the package.
- **version:**
  - **description:** The version of the inputted package. Note that this will return the highest version found if multiple packages are found.
- **packageid:**
  - **description:** The package ID of the package providing the version variable.
- **minimum_os_version:**
  - **description:** The minimum OS version if supplied.
- **installed_size:**
  - **description:** The size of the app when installed (in kilobytes).
- **installer_item_size:**
  - **description:** The size of the package (in bytes).

# SMBMounter

## Description

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

## Description

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

## Description

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

# VersionRegexGenerator

## Description

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
