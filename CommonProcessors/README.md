# Common Processors

To use these processors, add the processor as so:

    com.github.grahampugh.recipes.commonprocessors/NameOfProcessor

## Index

-   [ChangeModeOwner](#ChangeModeOwner)
-   [ChoicesXMLGenerator](#ChoicesXMLGenerator)
-   [JSSRecipeReceiptChecker](#JSSRecipeReceiptChecker)
-   [NSURLDownloader](#NSURLDownloader)
-   [SMBMounter](#SMBMounter)
-   [SMBUnmounter](#SMBUnmounter)
-   [StringReplacer](#StringReplacer)
-   [VersionRegexGenerator](#VersionRegexGenerator)

# ChangeModeOwner

## Description

Similar to the `ChangeMode` Processor, but also has the ability to change the owner.

## Input variables

-   **resource_path:**

    -   **required:** True
    -   **description:** Pathname of file/folder.

-   **mode:**

    -   **required:** False
    -   **description:** chown(1) owner string to apply to file/folder, e.g. "root".

-   **owner:**

    -   **required:** False
    -   **description:** chmod(1) mode string to apply to file/folder, e.g. "o-w", "755".

-   **group:**
    -   **required:** False
    -   **description:** chown(1) group string to apply to file/folder, e.g. "wheel".

## Output variables

-   None

# ChoicesXMLGenerator

## Description

Generates a `choices.xml` file for use with an installer. A postinstall script is required to run the installer with the `choices.xml.`

## Input variables

-   **choices_pkg_path:**

    -   **required:** True
    -   **description:** Path to start looking for files.

-   **desired_choices:**

    -   **required:** False
    -   **description:** A dictionary of choices.
    -   **default:** `""`

-   **choices_xml_dest:**
    -   **required:** False
    -   **description:** Path to save the choices.xml file. The processor will not do anything if none is provided.

## Output variables

-   None

# JSSRecipeReceiptChecker

An AutoPkg processor which works out the latest receipt (by date) from a different AutoPkg recipe, and provides useful values from its contents, which can be used to run a different recipe based on those values.

## Description

## Input variables

-   **name:**

    -   **required:** True
    -   **description:** This value should be the same as the `NAME` in the recipe from which we want to read the receipt. This is all we need to construct the override path.

-   **cache_dir:**
    -   **required:** False
    -   **description:** Path to the cache dir.
    -   **default:** `~/Library/AutoPkg/Cache`

## Output variables

-   **pkg_path:**

    -   **description:** Value of `pkg_path` obtained from the latest receipt.

-   **version:**

    -   **description:** Value of `version` obtained from the latest receipt.

-   **CATEGORY:**

    -   **description:** Value of `CATEGORY` obtained from the latest receipt.

-   **SELF_SERVICE_DESCRIPTION:**
    -   **description:** Value of `SELF_SERVICE_DESCRIPTION` obtained from the latest receipt.

# NSCURLDownloader

## Description

An experimental replacement for URLDownloader that uses `nscurl` instead of `curl` to provide a more native download experience. Only designed to be used if `URLDownloader` is not working.

## Input variables

-   **url:**

    -   **required:** True
    -   **description:** The URL to download.

-   **download_dir:**

    -   **required:** False
    -   **description:** The directory where the file will be downloaded to. Defaults to RECIPE_CACHE_DIR/downloads.

-   **filename:**

    -   **required:** False
    -   **description:** Filename to override the URL's tail.

-   **CHECK_FILESIZE_ONLY:**

    -   **default:** False
    -   **required:** False
    -   **description:** If True, a server's ETag and Last-Modified headers will not be checked to verify whether a download is newer than a cached item, and only Content-Length (filesize) will be used. This is useful for cases where a download always redirects to different mirrors, which could cause items to be needlessly re-downloaded. Defaults to False.

-   **PKG:**
    -   **required:** False
    -   **description:** Local path to the pkg/dmg we'd otherwise download. If provided, the download is skipped and we just use this package or disk image.

## Output Variables

-   **pathname:**
    -   **description:** Path to the downloaded file.
-   **last_modified:**
    -   **description:** last-modified header for the downloaded item.
-   **etag:**
    -   **description:** etag header for the downloaded item.
-   **download_changed:**
    -   **description:** Boolean indicating if the download has changed since the last time it was downloaded.
-   **nscurl_downloader_summary_result:**
    -   **description:** Description of interesting results.

# SMBMounter

## Description

Mounts an SMB directory. Expects a full SMB path as would be presented to `mount_smbfs`, because that's what it uses to mount. Valid examples:

    //server/share
    //server.com/share/subfolder/subsubfolder
    //user:password@server.com:123/share
    //DOMAIN;user:password@server/share

## Input variables

-   **smb_path:**

    -   **required:** True
    -   **description:** SMB path including pre-slashes but excluding `smb:`.

-   **mount_point:**
    -   **required:** False
    -   **description:** Output of `found_filenames` from the `SubDirectoryList` processor. Would require overriding if using the processor to mount more than one share.
    -   **default:** `/tmp/tmp_autopkg_mount`

## Output variables

-   None

# SMBUnmounter

## Description

Unmounts an SMB directory. Will fail if not following the `SMBMounter` processor.

## Input variables

-   **mount_point:**

    -   **required:** True
    -   **description:** A mount point. Required, normally would be passed through from the `SMBMounter` processor.
    -   **default:** `/tmp/tmp_autopkg_mount`

-   `mount_point`: A mount point. Required, should be passed through from the `SMBMounter` processor.

## Output variables

-   None

# StringReplacer

## Description

This processor replaces a string within a variable with another string, rather like using `sed`.
An example would be to remove a file suffix from a string.

## Input variables

-   **input_string:**

    -   **required:** True
    -   **description:** A string to be processed, e.g. `filename.dmg`.

-   **string_to_replace:**

    -   **required:** True
    -   **description:** The part of the `input_string` to be replaced, e.g. `.dmg`.

-   **replacement_string:**

    -   **required:** False
    -   **description:** The string that should replace instances of `string_to_replace`. This can be left as an empty string if the purpose is to remove instances of `string_to_replace`.
    -   **default:** `""`

## Output variables

-   **output_string:**
    -   **description:** The processed string.

# VersionRegexGenerator

## Description

A processor for generating a regex which matches the inputted version string or any possible higher version. Useful for generating a string which can be added to the criterion of Jamf Pro Smart Groups so that only older versions of an application cause a computer to go in or out of scope.

This processor uses an amended version of `Match Version Number Or Higher.bash` by William Smith, a shell script which determines a regex string of the current or any possible higher version number from an inputted version string. the original version of this file was published as a Gist at [https://gist.github.com/2cf20236e665fcd7ec41311d50c89c0e](https://gist.github.com/2cf20236e665fcd7ec41311d50c89c0e). The amendments were necessary to provide a "quiet" output mode which prints only the version regex string(s) without any additional outputs.

Note that for very complicated version strings, the regex may exceed 255 characters. Jamf Pro cannot accept strings longer than 255 characters, so this processor will create multiple regex strings that can be added as additional criteria in a smart group. Your subsequent processor design will have to accommodate this, so beware when using a version string that is on the cusp of generating a 255 character regex string, in case a change means that the first regex string no longer accounts for all possibilities.

## Input variables

-   **version:**

    -   **required:** True
    -   **description:** A version string with which to generate a regex that matches the version or higher.
    -   **default:** `2`

-   **path_to_match_version_number_or_higher_script:**

    -   **required:** False
    -   **description:** The full path to the file `match-version-number-or-higher.bash`. The processor will look for the file in your `RECIPE_DIR` (RecipeOverrides folder) and in `RECIPE_SEARCH_DIRS`. The file is also provided in the same folder as the `VersionRegexGenerator` processor.

## Output variables

-   **version_regex:**

    -   **description:** The version regex (maximum length 255 characters).

-   **version_regex_2:**

    -   **description:** An additional version regex for very complicated version strings, since Jamf cannot manage strings of more than 255 characters. Or `^$` if not required.

-   **version_regex_3:**
    -   **description:** An additional version regex for extremely complicated version strings, since Jamf cannot manage strings of more than 255 characters. Or `^$` if not required.
