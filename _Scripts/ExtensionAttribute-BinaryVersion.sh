#!/bin/bash

:<<DOC
ExtensionAttribute-BinaryVersion.sh
by Graham Pugh

This script checks the version of a binary and returns it as an extension attribute result.
DOC

BINARY="%BINARY_PATH%"
VERSION_ARGUMENT="%VERSION_ARGUMENT%"

version=""
if [ -f "$BINARY" ]; then
    version=$("$BINARY" $VERSION_ARGUMENT 2>&1 | head -n 1 | sed 's/[^0-9.]*\([0-9.]*\).*/\1/')
fi
echo "<result>$version</result>"
exit 0
