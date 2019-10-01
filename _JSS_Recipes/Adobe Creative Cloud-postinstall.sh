#!/bin/bash
## postinstall script to configure CCDA to show applications


ServiceConfig=<<'EOF'
<config>
    <panel>
        <name>AppsPanel</name>
        <visible>true</visible>
    </panel>
    <feature>
        <name>SelfServeInstalls</name>
        <enabled>true</enabled>
    </feature>
</config>
EOF

echo "$ServiceConfig" > "/Library/Application Support/Adobe/OOBE/Configs/ServiceConfig.xml"

exit
