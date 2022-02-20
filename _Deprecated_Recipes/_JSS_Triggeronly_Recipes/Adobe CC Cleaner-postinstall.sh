#!/bin/bash
## postinstall script to configure CCDA to show applications

# remove any existing version of the tool
rm -rf /Applications/Utilities/Adobe\ Creative\ Cloud\ Cleaner\ Tool.app ||:
mv /Applications/Adobe\ Creative\ Cloud\ Cleaner\ Tool.app /Applications/Utilities/Adobe\ Creative\ Cloud\ Cleaner\ Tool.app
# run the cleaner tool to remove EVERYTHING!
/Applications/Utilities/Adobe\ Creative\ Cloud\ Cleaner\ Tool.app/Contents/MacOS/Adobe\ Creative\ Cloud\ Cleaner\ Tool --removeAll=All --eulaAccepted=1

# delete the folders that remain
rm -rf /Applications/Utilities/Adobe\ Application\ Manager ||:
rm -rf /Applications/Utilities/Adobe\ Installers ||:
rm -rf /Library/Application\ Support/Adobe ||:
