#!/bin/bash

:<<DOC
xcode_command_line_tools-EA.sh
by Graham Pugh

This script checks if the Xcode Command Line Tools are installed and functional

Acknowledgements:
Excerpts from https://github.com/grahampugh/run-munki-run
which in turn borrows from https://github.com/tbridge/munki-in-a-box
DOC

installCommandLineTools() {
    # Installing the Xcode command line tools on 10.10+
    # This section written by Rich Trouton.
    cmd_line_tools_temp_file="/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress"

    # Installing the latest Xcode command line tools on 10.9.x or above
    osx_vers=$(sw_vers -buildVersion)
    if [[ "${osx_vers:0:2}" -ge 13 ]] ; then

        # Create the placeholder file which is checked by the softwareupdate tool
        # before allowing the installation of the Xcode command line tools.
        ${LOGGER} "Creating the Xcode CLT placeholder file..."
        echo "Creating the Xcode CLT placeholder file..."
        echo
        touch "$cmd_line_tools_temp_file"

        # Find the last listed update in the Software Update feed with "Command Line Tools" in the name
        cmd_line_tools=$(softwareupdate -l | grep "Label: Command Line Tools" | sed 's|^\* Label: ||')

        # Install the command line tools
        if [[ $cmd_line_tools ]]; then
            ${LOGGER} "Running softwareupdate to downoload the Xcode Command Line Tools..."
            echo "Running softwareupdate to downoload the Xcode Command Line Tools..."
            echo
            softwareupdate -i "$cmd_line_tools"
        else
            ${LOGGER} "ERROR: Xcode Command Line Tools not found in software catalog."
            echo "ERROR: Xcode Command Line Tools not found in software catalog."
            echo
            exit 5
        fi

        # Remove the temp file
        if [[ -f "$cmd_line_tools_temp_file" ]]; then
            rm "$cmd_line_tools_temp_file"
        fi
    else
        echo "ERROR: this script is only for use on OS X/macOS >= 10.9"
        exit 5
    fi
}

## Main section

# Commands
GIT="/usr/bin/git"
XCODESELECT="/usr/bin/xcode-select"

# Check for Command line tools.
if ! $XCODESELECT -p >/dev/null 2>&1 ; then
    xclt_installed=0
else
    xclt_installed=1
fi

# check CLI tools are functional
if ! $GIT --version >/dev/null 2>&1 ; then
    xclt_functional=0
else
    xclt_functional=1
fi

if [[ $xclt_functional = 1 ]]; then
    echo "<result>functional</result>"
elif [[ $xclt_installed = 1 ]]; then
    echo "<result>needs reinstall</result>"
else
    echo "<result>not installed</result>"
fi

exit 0