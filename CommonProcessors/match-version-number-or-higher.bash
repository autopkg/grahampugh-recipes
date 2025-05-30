#!/bin/bash

: <<ABOUT_THIS_SCRIPT
-------------------------------------------------------------------------------

	Written by:William Smith
	Professional Services Engineer
	Jamf
	bill@talkingmoose.net
	https://gist.github.com/2cf20236e665fcd7ec41311d50c89c0e
	
	Originally posted: April 12, 2020
	
	Modified: May 6, 2020
	Changes:
	Adding support to break long regex strings for Jamf Pro.
	
	Modified: May 24, 2020
	Changes:
	Displaying sequence characters in verbose reporting instead of number.
	Now accounting for version strings with non-numeric characters.
	Added warning if sequence begins with "0".
	Added warning if sequence contains non-standard characters.
	Accounting for multple Jamf Pro regex strings.

	Modified September 9, 2020 by Graham Pugh
	Changes:
	Allowed verbose and using Jamf modes to be called from the command line.
	Added quiet mode which suppresses all output except the regex itself.

	Modified 30 May, 2025 by Graham Pugh
	Changes:
    Rewrote the logic for splitting the regex for Jamf Pro to use awk. This
	allows the regex to be split at the pipe character (|) while ensuring that
	the regex does not exceed the character limit for Jamf Pro fields.

	Purpose: Generate a regular expression (regex) string that matches
	the provided version number or higher.
	
	Instructions: see '/path/to/match-version-number-or-higher.bash' -h
	
	Or run the script in Terminal without any argument to use the example
	version number string within the script.
	
	Optionally, set verbose to On using -v or --verbose.

	To output only the regex without any warnings, explanation or blank lines, 
	run with the -q or --quiet option.

	Except where otherwise noted, this work is licensed under
	http://creativecommons.org/licenses/by/4.0/

	"Perhaps it is the forgetting not the remembering that is the essence
	of what makes us human. To make sense of the world, we must filter it."
	
-------------------------------------------------------------------------------
ABOUT_THIS_SCRIPT

# ----- get command line arguments ---------------------

# defaults
# turn on for step-by-step explanation while building the regex or off to provide only the regex
verbose="false" # "true" or "false"
# turn on for a single line output
quietMode="false" # "true" or "false"
usingJamf="false" # "true" or "false"
jamfCharacterLimit="251" # Jamf Pro field character limit, set to 255 but leaving room for ^() and )$ characters

# get arguments
while test $# -gt 0
do
    case "$1" in
        -v|--verbose) verbose="true"
        ;;
        -q|--quiet) quietMode="true"
        ;;
        -j|--usingJamf) usingJamf="true"
        ;;
        -h|--help|-*)
            echo "
Generate a regular expression (regex) string that matches
the provided version number or higher.

Usage:
./match-version-number-or-higher.bash [--help] [--verbose] [--usingJamf] [versionString]

-h | --help         Displays this text
-v | --verbose      Show a step-by-step explanation while building the regex 
-q | --quiet        Suppress all output except the regex itself 
-j | --usingJamf    Split regex to accommodate Jamf's 255 character limit 
*                   The version string, e.g. 10.12.2

Note if using -q and -j and the regex exceeds $jamfCharacterLimit characters, the full regex is not shown.
The output will be split into multiple lines. 
e.g. for Version string \"5.0.3 (24978.0517)\" the output is:

^(\d{2,}.*|[6-9].*|5\.\d{2,}.*|5\.[1-9].*|5\.0\.\d{2,}.*|5\.0\.[4-9].*|5\.0\.3 \(\d{6,}.*|5\.0\.3 \([3-9]\d{4,}.*)$
^(5\.0\.3 \(2[5-9]\d{3,}.*|5\.0\.3 \(249[8-9]\d{1,}.*|5\.0\.3 \(24979.*|5\.0\.3 \(24978\.\d{5,}.*|5\.0\.3 \(24978\.[1-9]\d{3,}.*|5\.0\.3 \(24978\.0[6-9]\d{2,}.*|5\.0\.3 \(24978\.05[2-9]\d{1,}.*|5\.0\.3 \(24978\.051[8-9].*|5\.0\.3 \(24978\.0517\).*)$
"
            exit 0
        ;;
		*)
			versionString=$1		
        ;;
    esac
    shift
done

# verbose mode trumps quiet mode
if [[ $verbose == "true" ]]; then
	quietMode="false"
fi

# ----- set verbosity and provide a version number string ---------------------

# confirm version string only contains numbers and periods or is blank
if [[ $versionString =~ [^[:digit:].] ]]; then
	warning="Yes"
fi

# sample version strings
if [[ "$versionString" = "" ]]; then
	# versionString="79.0.3945.117" # e.g. Google Chrome
	# versionString="16.17" # Microsoft Office 2019
	# versionString="74.0.1" # Mozilla Firefox
	# versionString="19.10.2.41" # Citrix Workspace
	# versionString="20.006.20034" # Adobe Acrobat Reader DC
	# versionString="19.021.20058" # Adobe Acrobat Pro DC
	# versionString="21.0.3" # Adobe Photoshop 2020
	# versionString="100.86.91" # Microsoft Defender
	# versionString="5.0.3 (24978.0517)" # Zoom.us
	versionString="5.0.3-24978.0517 (4323)" # just a long and complicated test string
fi

# ----- functions -------------------------------------------------------------
	
# enables or disables verbose mode
logcomment() {
	if [[ "$verbose" == "true" ]]; then
		echo "$1"
	fi
}

# processes a digit within a sequence
evaluateSequence()	{

	# ----- process the first digit in a sequence -----------------------------

	# prepend exact characters leading up to the current character under evaluation
	if [[ "$regex" != "" ]]; then
		regex="$regex|"
	fi

	# get the sequence ( e.g. "74" of "74.0.1" )
	sequence=$( /usr/bin/awk -F "." -v i=$aSequence '{ print $i }' <<< "$adjustedVersionString" )
	logcomment "Sequence $aSequence is \"$sequence\""
	
	# show warning if sequence begins with "0"
	if [[ "$sequence" =~ ^0.+ ]]; then
		warning="Yes"
	fi
	
	# get count of digits in the sequence ( e.g. 2 digits in "74" )
	digitCount=$( /usr/bin/tr -d '\r\n' <<< "$sequence" | /usr/bin/wc -c | /usr/bin/xargs ) # e.g. 2
	logcomment "Count of digits in sequence \"$sequence\" is $digitCount"
	logcomment
	
	# generate regex for the first number of the sequence rolling over to add another digit ( e.g. 99 > 100 )
	logcomment "Count of digits in sequence \"$sequence\" may roll over to $((digitCount + 1)) or more digits"
	buildRegex="$regexPrefix\d{$((digitCount + 1)),}"
	logcomment "Regex for $((digitCount + 1)) or more digits is \"$buildRegex\""
	
	# add a wildcard to end of string to match everything else
	logcomment "Wildcard everything else"
	buildRegex="$buildRegex.*"
	
	# show complete regex for this digit
	logcomment "Complete regex is \"$buildRegex\""
	regex="$regex$buildRegex"
	
	# show the entire regex as the script progresses through each digit
	logcomment "Progressive regex: $regex"
	logcomment
	
	# ----- process the remaining digits in a sequence ------------------------
	
	# create array of digits in sequence ( e.g. "7, 4" )
	digits=()
	for ((i = 0; i < ${#sequence}; i++)); do
		digits+=("${sequence:$i:1}")
	done

	# iterate over each digit of the sequence
	# for aDigit in ${digits[*]}
	for indexNumber in "${!digits[@]}"
	do
		# ----- the number 8 can only roll up to 9 ----------------------------
		
		if [[ "${digits[$indexNumber]}" -eq 8 ]]; then
			logcomment "Because digit $((indexNumber + 1 )) in sequence \"$sequence\" is \"8\", roll it to \"9\""
			buildRegex="9"
			
			if [[ $((digitCount - indexNumber - 1 )) -ne 0 ]]; then			
				logcomment "Because remaining count of digits in sequence \"$sequence\" is $((digitCount - indexNumber - 1 )), pad the sequence with $((digitCount - indexNumber - 1 )) more digit(s)"
				buildRegex="$buildRegex\d{$((digitCount - indexNumber - 1 )),}"
				logcomment "Regex for $((digitCount - indexNumber - 1 )) more digit(s) is \d{$((digitCount - indexNumber - 1 )),}"
			fi
			
			logcomment "Wildcard everything else"
			buildRegex="$regexPrefix$buildRegex.*"
			logcomment "Complete regex is \"$buildRegex\""
			
			logcomment "Progressive regex: $regex|$buildRegex"
			regex="$regex|$buildRegex"
			logcomment
			
		# ----- anything 0 through 7 will roll up to the next number ----------
		
		elif [[ "${digits[$indexNumber]}" -lt 8 ]]; then
			logcomment "Because digit $((indexNumber + 1 )) in sequence \"$sequence\" is \"${digits[$indexNumber]}\", roll it to \"$((${digits[$indexNumber]} + 1))\" or higher"
			buildRegex="[$((${digits[$indexNumber]} + 1))-9]"
			logcomment "Regex for $((${digits[$indexNumber]} + 1)) or higher is \"$buildRegex\""
			
			if [[ $((digitCount - indexNumber - 1 )) -ne 0 ]]; then			
				logcomment "Because remaining count of digits in sequence \"$sequence\" is $((digitCount - indexNumber - 1 )), pad the sequence with $((digitCount - indexNumber - 1 )) more digit(s)"
				buildRegex="$buildRegex\d{$((digitCount - indexNumber - 1 )),}"
				logcomment "Regex for $((digitCount - indexNumber - 1 )) more digit(s) is \d{$((digitCount - indexNumber - 1 )),}"
			fi
			
			logcomment "Wildcard everything else"
			buildRegex="$regexPrefix$buildRegex.*"
			logcomment "Complete regex is \"$buildRegex\""
			
			logcomment "Progressive regex: $regex|$buildRegex"
			regex="$regex|$buildRegex"
			logcomment
		
		# ----- nothing to do if the digit is 9 -------------------------------
		# ----- (the preceding digit is already rolled up) --------------------
		
		else
			logcomment "Because \"Digit $((indexNumber + 1 ))\" in sequence \"$sequence\" is 9, do nothing"
			logcomment
		fi
		
		regexPrefix="$regexPrefix${digits[$indexNumber]}"
	done
}

# ----- run the script --------------------------------------------------------

# verify the version string to the user
logcomment "Version string is $versionString"

# replace non-numeric sequences of characters with periods
adjustedVersionString=$( /usr/bin/sed -E 's/[^0-9]+/./g' <<< "$versionString" | /usr/bin/sed -E 's/[^0-9]$//g' )
logcomment "Adjusted version string for parsing is \"$adjustedVersionString\""

# number of "sequences" separated by a divider
sequenceCount=$( /usr/bin/awk -F "." '{ print NF }' <<< "$adjustedVersionString" ) # e.g. 4
logcomment "Number of sequences is $sequenceCount"

# create a list of sequence dividers in the version string separated by "###"
sequenceDividers=$( /usr/bin/sed -E 's/[0-9]+/###/g' <<< "$versionString" )
logcomment "Replacing digits in sequences to get the sequence dividers \"$sequenceDividers\""
logcomment

# 14 special regex characters that may appear as sequence dividers that will need escaping
regexSpecialCharacters="\&$.|?*+()[]{}"

# used to track unchanged digits to the left of the current digit being evaluated
regexPrefix=""

# evaluate the version string
for ((aSequence=1;aSequence<=sequenceCount;aSequence++))
do
	logcomment "Evaluating sequence $aSequence of $sequenceCount"
	evaluateSequence
	
	# resetting variable
	dividers=""
	
	# add sequence divider to end of the sequence
	divider=$( /usr/bin/awk -F "###" -v divider=$(( aSequence + 1 )) '{ print $divider }' <<< "$sequenceDividers" )
	
	for (( aCharacter=0; aCharacter<${#divider}; aCharacter++ ))
	do
		logcomment "Next character is \"${divider:$aCharacter:1}\""
		
		if [[ "$regexSpecialCharacters" = *"${divider:$aCharacter:1}"* ]]; then
			dividers="$dividers\\${divider:$aCharacter:1}"
			logcomment "Escaping \"${divider:$aCharacter:1}\" to create \"\\${divider:$aCharacter:1}\""
			
		else
			dividers="$dividers${divider:$aCharacter:1}"
			logcomment "This character does not need escaping"
		fi
	done
	regexPrefix="$regexPrefix$dividers"
	logcomment "Progressive regex: $regex|$regexPrefix"
	logcomment
done

# include original version string at end of regex, escaping special regex characters
escapedVersionString=""
for (( aCharacter=0; aCharacter<${#versionString}; aCharacter++ ))
do
	
	if [[ "$regexSpecialCharacters" = *"${versionString:$aCharacter:1}"* ]]; then
		escapedVersionString="$escapedVersionString\\${versionString:$aCharacter:1}"
	else
		escapedVersionString="$escapedVersionString${versionString:$aCharacter:1}"
	fi
done

regex="$regex|$escapedVersionString"
logcomment "Adding original version string to end of regex as a potential match."
logcomment

if [[ "$warning" = "Yes" && "$quietMode" != "true" ]]; then
	echo
	echo "==============================================="
	echo "                                               "
	echo "                    WARNING                    "
	echo "                                               "
	echo "   This version string contains non-standard   "
	echo "   characters or number sequences that begin   "
	echo "   with a zero (i.e. \"0123\", which is the    "
	echo "   same as \"123\").                           "
	echo "                                               "
	echo "   Use regexes with caution.                   "
	echo "                                               "
	echo "==============================================="
fi
	
# return full regex including start and end of string characters (e.g. ^ and $ )
regex="^($regex.*)$"

# get characterCount of regex
regexCharacterCount=$( /usr/bin/wc -c <<< "$regex" | /usr/bin/xargs )

# display the regex for the version string and its character count
[[ "$quietMode" != "true" ]] && echo
[[ "$quietMode" != "true" ]] && echo "Regex for \"$versionString\" or higher ($regexCharacterCount characters):"
[[ ("$quietMode" == "true" && ("$usingJamf" == "true" && "$regexCharacterCount" -le $jamfCharacterLimit) || "$usingJamf" == "No") || "$quietMode" != "true" ]] && echo "$regex"
[[ "$quietMode" != "true" ]] && echo

if [[ "$usingJamf" == "true" && "$regexCharacterCount" -gt $jamfCharacterLimit ]]; then

	if [[ "$quietMode" != "true" ]]; then
		# print Jamf Pro instructions and both regex strings
		echo "Jamf Pro has a field character limit of 255 characters."
		echo "This regex exceeds that field character limit."
		echo "Add additional \"Application Version\" criteria to your search"
		echo "and paste each regex string into the the additional fields."
		echo
		echo "For example:"
		echo
		echo "              Application Title       is                Google Chrome.app"
		echo "and     (     Application Version     matches regex     <Regex 1>"
		echo "or            Application Version     matches regex     <Regex 2>     )"
		echo
	fi

	# get count of characters in generated regex string
	regexCharacters=${#regex}
	# determine number of regex strings needed, accounting for beginning ^ and ending $ characters
	jamfStringCount="$((regexCharacters / jamfCharacterLimit + 1))"
	split_len=$((regexCharacters / jamfStringCount))

	# Remove leading ^( and trailing )$
	regex_cleaned="${regex#^\(}"
	regex_cleaned="${regex_cleaned%\)\$}"

	awk -v maxlen=$split_len -v quiet="$quietMode" '
BEGIN {
  line = ""
  count = 1
}
{
  n = split($0, parts, /\|/)
  for (i = 1; i <= n; i++) {
    part = parts[i]
    # +1 for the pipe if line is not empty
    if (length(line part) + (length(line) > 0 ? 1 : 0) <= maxlen) {
      line = (length(line) ? line "|" part : part)
    } else {
      wrapped = "^(" line ")$"
      if (quiet == "true") {
        print wrapped
      } else {
        print "Regex " count
        print wrapped
        print "Length: " length(wrapped) " characters"
        print ""
      }
      count++
      line = part
    }
  }
}
END {
  if (length(line)) {
    wrapped = "^(" line ")$"
    if (quiet == "true") {
      print wrapped
    } else {
      print "Regex " count
      print wrapped
      print "Length: " length(wrapped) " characters"
    }
  }
}
' <<< "$regex_cleaned"
fi
