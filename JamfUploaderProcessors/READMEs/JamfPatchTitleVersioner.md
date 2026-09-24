# JamfPatchTitleVersioner
## Description

Determines the latest software version being reported by a Jamf Pro Patch Management Title.

## Input variables

- **JSS_URL:**
  - **required:** True
  - **description:** URL to a Jamf Pro server that the API user has write access to, optionally set as a key in the com.github.autopkg preference file.
- **API_USERNAME:**
  - **required:** True
  - **description:** Username of account with appropriate access to jss, optionally set as a key in the com.github.autopkg preference file.
- **API_PASSWORD:**
  - **required:** True
  - **description:** Password of api user, optionally set as a key in the com.github.autopkg preference file.
- **patch_softwaretitle**:
  - **required**: True
  - **description**: Name of the patch softwaretitle (e.g. 'Mozilla Firefox') used in Jamf.

## Output variables

- **latest_patch_version:**
  - **description:** The latest version number of the software reported by the Patch Title.
