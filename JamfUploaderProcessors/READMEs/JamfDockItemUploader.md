# JamfDockItemUploader

## Description

A processor for AutoPkg that will upload a dock item to a Jamf Cloud or on-prem server.

## Input variables

- **JSS_URL:****
  - **required:**** True
  - **description:**** URL to a Jamf Pro server that the API user has write access to, optionally set as a key in the com.github.autopkg preference file.
- **API_USERNAME:****
  - **required:**** True
  - **description:**** Username of account with appropriate access to jss, optionally set as a key in the com.github.autopkg preference file.
- **API_PASSWORD:****
  - **required:**** True
  - **description:**** Password of api user, optionally set as a key in the com.github.autopkg preference file.
- **dock_item_name:**
  - **required:** True
  - **description:** Name of the dock item e.g. 'Safari'.
- **dock_item_type:**
  - **required:** True
  - **description:** Type of the dock item - either 'App', 'File' or 'Folder'.
- **dock_item_path:**
  - **required:** True
  - **description:** Path of the dock item e.g. 'file:///Applications/Safari.app/'
- **replace_dock_item:**
  - **required:** False
  - **description:** Replace existing dock items?
  - **default:** False

## Output variables

- **dock_item:****
  - **description:**** The created/updated dock item.
- **jamfcategoryuploader_summary_result:**
  - **description:** Summary of created dock items.
  - **example:**
    ```
    The following dock items were created or updated in Jamf Pro:
    Dock Item Id  Dock Item Name  Dock Item Type  Dock Item Path
    ------------  --------------  --------------  --------------
    9             Safari          App             file:///Applications/Safari.app/
    ```

## Usage in policy templates

Created dock items can be used in policy templates after uploading them.

### Example

Example of using JamfDockItemUploader in combination with JamfPolicyUploader:

#### Recipe:
```yaml
[...]

Process:
  - Processor: com.github.grahampugh.jamf-upload.processors/JamfDockItemUploader
    Arguments:
      dock_item_name: '%DOCK_ITEM_NAME%'
      dock_item_type: '%DOCK_ITEM_TYPE%'
      dock_item_path: '%DOCK_ITEM_PATH%'
      replace_dock_item: True

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfCategoryUploader
    Arguments:
      category_name: '%CATEGORY%'

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPackageUploader
    Arguments:
      pkg_category: '%CATEGORY%'

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPolicyUploader
    Arguments:
      policy_name: '%POLICY_NAME%'
      policy_template: '%POLICY_TEMPLATE%'
      replace_policy: '%POLICY_REPLACE%'
      icon: '%NAME%.png'
```

#### Policy Template

**Note:** You need to define the 'action' of the dock item. Either 'Add To End', 'Add To Beginning' or 'Remove'.

```yaml
<?xml version="1.0"?>
<policy>
	<general>
		<name>%POLICY_NAME%</name>
		<enabled>true</enabled>
		<frequency>Ongoing</frequency>
		<category>
			<name>%POLICY_CATEGORY%</name>
		</category>
		<trigger_other>%POLICY_NAME%</trigger_other>
	</general>
	<scope>
		<all_computers>true</all_computers>
	</scope>
	<package_configuration>
		<packages>
			<size>1</size>
			<package>
				<name>%pkg_name%</name>
				<action>Install</action>
			</package>
		</packages>
	</package_configuration>
	<scripts>
	</scripts>
  <dock_items>
    <size>1</size>
    <dock_item>
      <name>%DOCK_ITEM_NAME%</name>
      <action>Add To End</action>
    </dock_item>
  </dock_items>
  <maintenance>
    <recon>true</recon>
	</maintenance>
</policy>
```
