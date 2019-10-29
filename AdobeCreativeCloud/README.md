Adobe Creative Cloud AdobeCCDAFromConsoleForJamfPro.pkg recipe
===============================

This recipe is designed to repackage the Adobe Creative Cloud Desktop Application installer package that is generated in the Adobe Admin Console. This is necessary to make the package installable via Jamf Pro.

This recipe has no parent `.download` recipe, since that is a manual process. You have to provide the path to a downloaded zip file from the Adobe admin console. You also need to provide a version number, as this is not extractable from the package. Therefore, to run this recipe, you need to run as follows:

    autopkg run "AdobeCCDAFromConsoleForJamfPro.pkg" --key pathname=/path/to/Adobe_CCDA_downloaded.zip --key version=5.0.0.354
