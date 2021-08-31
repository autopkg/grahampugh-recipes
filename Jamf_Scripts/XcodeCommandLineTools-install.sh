#!/bin/bash

:<<DOC
xcode_command_line_tools_install.sh
by Graham Pugh

This script automates the installation of the latest version
of the Xcode Command Line Tools

Acknowledgements:
Excerpts from https://github.com/grahampugh/run-munki-run
which in turn borrows from https://github.com/tbridge/munki-in-a-box
DOC

HELP=<<HELP
Usage:
./xcode_command_line_tools_install.sh +

-c | --check        check only, do not install
-h | --help         display this text
HELP


rootCheck() {
    # Check that the script is running as root
    if [[ ! $EUID -eq 0 ]]; then
        $LOGGER "ERROR: Script is not being run as root"
        echo "ERROR: This script is meant to run as root."
        echo "Please run with sudo or from a root process."
        echo
        exit 4 # Not running as root.
    fi
}

installCommandLineTools() {
    # Installing the Xcode command line tools on 10.10+
    # This section written by Rich Trouton.
    cmd_line_tools_temp_file="/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress"

    # Installing the latest Xcode command line tools on 10.9.x or above
    osx_vers=$(sw_vers -buildVersion)
    if [[ "${osx_vers:0:2}" -ge 13 ]] ; then

        # Create the placeholder file which is checked by the softwareupdate tool
        # before allowing the installation of the Xcode command line tools.
        $LOGGER "Creating the Xcode CLT placeholder file..."
        echo "Creating the Xcode CLT placeholder file..."
        echo
        touch "$cmd_line_tools_temp_file"

        # Find the last listed update in the Software Update feed with "Command Line Tools" in the name
        cmd_line_tools=$(softwareupdate -l | grep "Label: Command Line Tools" | sed 's|^\* Label: ||')

        # Install the command line tools
        if [[ $cmd_line_tools ]]; then
            $LOGGER "Running softwareupdate to downoload the Xcode Command Line Tools..."
            echo "Running softwareupdate to downoload the Xcode Command Line Tools..."
            echo
            softwareupdate -i "$cmd_line_tools"
        else
            $LOGGER "ERROR: Xcode Command Line Tools not found in software catalog."
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

# logger
LOGGER="/usr/bin/logger -t Xcode_CLT_Setup"

# get arguments
check_only=0
while test $# -gt 0
do
    case "$1" in
        -c|--check)
            check_only=1
        ;;
        *)
            echo "$HELP"
            exit 0
        ;;
    esac
    shift
done

# Check for Command line tools.

if ! $XCODESELECT -p >/dev/null 2>&1 ; then
    if [[ $check_only = 0 ]]; then
        installCommandLineTools
    else
        $LOGGER "Xcode Command Line Tools not installed"
        echo
        echo "Xcode Command Line Tools not installed. Run without -c to install"
    fi
fi

# check CLI tools are functional
if ! $GIT --version >/dev/null 2>&1 ; then
    if [[ $check_only = 0 ]]; then
        installCommandLineTools
    else
        $LOGGER "Xcode Command Line Tools not functional"
        echo
        echo "Xcode Command Line Tools not functional. Run without -c to re-install"
    fi
else
    $LOGGER "Xcode Command Line Tools installed and functional"
    echo
    echo "Xcode Command Line Tools installed and functional"
    exit 0
fi

# double-check CLI tools are functional
if ! $GIT --version >/dev/null 2>&1 ; then
    if [[ $check_only = 0 ]]; then
        $LOGGER "ERROR: Xcode Command Line Tools failed to install"
        echo
        echo "ERROR: Xcode Command Line Tools failed to install."
        exit 1
    fi
else
    $LOGGER "Xcode Command Line Tools installed and functional"
    echo
    echo "Xcode Command Line Tools installed and functional"
fi

exit 0