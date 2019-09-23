#!/bin/bash

# Remove existing JDK 8 installations

for JAVADIR in "$3"/Library/Java/JavaVirtualMachines/jdk1.8.0_*; do
  rm -rf "$JAVADIR"
done

exit 0
