#!/bin/bash
## postinstall script to run adobe-licensing-toolkit

# See https://helpx.adobe.com/enterprise/using/recover-sdl-licenses.html
# for other options

# run the adobe-licensing-toolkit to deactivate licenses
/bin/chmod 755 /Library/Management/Adobe/adobe-licensing-toolkit
/usr/sbin/chown root:admin /Library/Management/Adobe/adobe-licensing-toolkit
/Library/Management/Adobe/adobe-licensing-toolkit --deactivate
