# JamfPackageUploader

## Description

A processor for AutoPkg that will upload a package to a JCDS or File Share Distribution Point.

Can be run as a post-processor for a pkg recipe or in a child recipe. The parent (pkg) recipe must output pkg_path as this is a required key.

## Input variables

- **pkg_name:**
  - **required:** False
  - **description:** Package name. If supplied, will rename the package supplied in the pkg_path key when uploading it to the fileshare.
- **pkg_path:**
  - **required:** False
  - **description:** Path to a pkg or dmg to import - \*\*provided by previous pkg recipe/processor.
- **version:**
  - **required:** False
  - **description:** Version string - \*\*provided by previous pkg recipe/processor.
- **pkg_category:**
  - **required:** False
  - **description:** Package category
- **pkg_info:**
  - **required:** False
  - **description:** Package info field
- **pkg_notes:**
  - **required:** False
  - **description:** Package notes field
- **pkg_priority:**
  - **required:** False
  - **description:** Package priority.
  - **default:** 10
- **reboot_required:**
  - **required:** False
  - **description:** Whether a package requires a reboot after installation.
  - **default:**
- **os_requirements:**
  - **required:** False
  - **description:** Package OS requirement
- **required_processor:**
  - **required:** False
  - **description:** Package required processor. Acceptable values are 'x86' or 'None'
  - **default:** None
- **send_notification:**
  - **required:** False
  - **description:** Whether to send a notification when a package is installed.
  - **default:** 'False'
- **replace_pkg:**
  - **required:** False
  - **description:** Overwrite an existing package if True.
  - **default:** False
- **replace_pkg_metadata:**
  - **required:** False
  - **description:** Overwrite existing package metadata and continue if True, even if the package object is not re-uploaded.
  - **default:** False
- **skip_metadata_upload:**
  - **required:** False
  - **description:** For Jamf Cloud customers, skip the upload of package metadata. This allows a new package to be uploaded but will not write any metadata such as SHA512 hash, category, info, etc. This allows upload of packages with just `create` and `read` privileges on package objects (otherwise `update` rights are also required). Not for use by self-hosted Jamf customers, and not relevant in conjunction with `jcds_mode`. Note that `replace_package` key is not functional if `skip_metadata_upload` is set.
  - **default:** False
- **jcds_mode:**
  - **required:** False
  - **description:** Upload package using JCDS mode.
  - **default:** False
- **JSS_URL:**
  - **required:** True
  - **description:** URL to a Jamf Pro server that the API user has write access to, optionally set as a key in the com.github.autopkg preference file.
- **API_USERNAME:**
  - **required:** True
  - **description:** Username of account with appropriate access to jss, optionally set as a key in the com.github.autopkg preference file.
- **API_PASSWORD:**
  - **required:** True
  - **description:** Password of api user, optionally set as a key in the com.github.autopkg preference file.
- **SMB_URL:**
  - **required:** False
  - **description:** URL to a Jamf Pro fileshare distribution point which should be in the form `smb://server/share`. If you have multiple SMB shares you wish to mount, you can separate those urls with ';;' (ex. `smb://xsrv1.example.com/CasperShare;;smb://xsrv2.example.com/Caspershare`) and the uploader will iterate over that list.
- **SMB_USERNAME:**
  - **required:** False
  - **description:** Username of account with appropriate access to jss, optionally set as a key in the com.github.autopkg preference file. If you have multiple SMB shares you wish to mount that have different usernames, you can separate those usernames with ';;' (ex. `xsrvupload1;;xsrvupload2`) in the corresponding order to your SMB_URL list, otherwise the same account will be used for all SMB endpoints.
- **SMB_PASSWORD:**
  - **required:** False
  - **description:** Password of api user, optionally set as a key in the com.github.autopkg preference file. If you have multiple SMB shares you wish to mount that have different passwords, you can separate those passwords with ';;' (ex. `xsrvpw1;;xsrvpw2`) in the corresponding order to your SMB_URL list, otherwise the same account will be used for all SMB endpoints.

## Output variables

- **pkg_path:**
  - **description:** The path of the package as provided from the parent recipe.
- **pkg_name:**
  - **description:** The name of the uploaded package.
- **pkg_uploaded:**
  - **description:** True/False depending if a package was uploaded or not.
- **jamfpackageuploader_summary_result:**
  - **description:** Description of interesting results.
