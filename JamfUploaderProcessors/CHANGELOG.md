# CHANGELOG

The dates here represent when the features were added to the processors in the `jamf-upload` repo.

## 2024-10-17

* Fixed an issue with `JamfPackageUploader` where if there was both a SMB share set and a cloud DP (using `CLOUD_DP`), the cloud upload would attempt (and fail) to uplaod using the old `dbfileupload` method on servers running 11.5+.

## 2024-10-06

* Added the `JamfPackageRecalculator` processor.
* Added the `recalculate` option to the `JamfPackageUploader`. Note that this will do a full package recalculation after every package upload on Jamf Pro version 11.10 and above. Depending on your workflow, it may be more efficient to leave this unset and run the `JamfPackageRecalculator` in a separate recipe/step at the end of your recipe list.

## 2024-08-30

* Added the `JamfComputerGroupDeleter` processor.

## 2024-05-13

* Added a Jamf Pro version check, so that the `pkg_api_mode` option becomes default for `JamfPackageUploader` processor when none of `jcds2_mode`, `aws_cdp_mode, or a separate File Share Distribution Point are specified.

## 2024-04-03

* Added the `pkg_api_mode` option to the `JamfPackageUploader` processor, which uses the new `v1/packages` endpoint to upload packages.

## 2024-03-11

* Added an `rstrip` to the `JSS_URL` ingest to prevent errors if someone adds a trailing slash to the URL.

## 2024-03-08

* Added `aws_cdp_mode` to `JamfPackageUploader`.
* Added `JamfPatchChecker` procesor (#130, thanks @pandemicus).

## 2024-02-19

* Added second check for bearer token before uploading pkg metadata in `JamfPackageUploaderBase`.
* Fixed path to token file in env so an existing token will be used if found.
* Added `ea_description` option to `JamfExtensionAttributeUploader` (#125, thanks @jamesfkane).
* Added the `skip_script_key_substitution` option to `JamfExtensionAttributeUploader` (#128, thanks @davidbpirie).

## 2023-10-24

* Refactored all JamfUploader processors to use a Base class.
* Removed `jcds_mode` from `JamfPackageUploader` as it has been rendered unworkable by Jamf.

## 2023-10-21

* Added the `JamfMobileDeviceProfileUploader` and `JamfMobileDeviceGroupUploader` processors.

## 2023-10-13

* Added the ability to retain existing scope for `JamfComputerProfileUploader` and `JamfPolicyUploader`.

## 2023-08-03

* Removed Basic Auth for endpoints, added OAuth method for obtaining token.

## 2023-07-14

* Add `jcds2_mode` to `JamfPackageUploader`.
  
## 2023-06-23

* Fix key substitution in `JamfComputerProfileUploader` to prevent it overwriting the original template.

## 2023-06-10

* Check for token for every package processed by `JamfPackageCleaner`.
* Add `pkg_display_name` key to `JamfPackageUploader`.
* Add `dry_run` key to `JamfPackageCleaner`.

## 2023-04-26

* Add `skip_script_key_substitution` key to `JamfScriptUploader`.

## 2023-04-25

* Add `JamfPackageCleaner`.

## 2023-04-12

* Allow randomised failover URL for `jcds_mode` in `JamfPackageUploader`.

## 2022-12-20

* Allow relative paths to templates.
* Allow skip template in `JamfPatchUploader`.

## 2022-11-14

* All shebangs updated to use the AutoPkg python distribution.

## 2022-10-15

* Allow multiple SMB repos plus SMB + Cloud in `JamfPackageUploader`.

## 2022-10-08

* Fail properly for unsubstitutable variables.
* Fail properly if cannot detemine the Jamf Pro version.

## 2022-09-21

* Allow empty values for substitutable variables.

## 2022-08-25

* Add `sleep` to all relevant processors.

## 2022-06-24

* Add `skip_metadata_upload` in `JamfPackageUploader`.

## 2022-02-25

* Add `jcds_mode` in `JamfPackageUploader`.

## 2022-01-31

* Fix script url and add 405 error.

## 2021-10-22

* Switch to token auth for Jamf Classic API, and move common functions into `JamfUploaderBase.py`.
* URL fixes.
  
## 2021-10-21

* Fixes for variable substitution.

## 2021-09-01

* Limit file search within repos.

## 2021-08-24

* Add AWS cookie checks.

## 2021-08-22

* Remove case-sensitivity of object name check.

## 2021-05-04

* Add `JamfComputerProfileUploader` processor, plus fix for #52.

## 2021-04-06

* Enable HTTP/2 transfer.
