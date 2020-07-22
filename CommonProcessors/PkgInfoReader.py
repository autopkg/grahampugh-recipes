#!/usr/bin/env python
#
# Copyright 2020 Graham Pugh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This code is adapted largely from Munki's pkgutils.py, written by Greg Neagle:
#
#     https://github.com/munki/munki/blob/main/code/client/munkilib/pkgutils.py


import glob
import os
import re
import shutil
import subprocess
import tempfile
from xml.dom import minidom
from urllib.parse import unquote

from autopkglib import APLooseVersion  # pylint: disable=import-error
from autopkglib import Processor, ProcessorError  # pylint: disable=import-error
from autopkglib.Copier import Copier  # pylint: disable=import-error

import plistlib

__all__ = ["PkgInfoReader"]


class PkgInfoReader(Copier):
    """This processor looks for information in packages with the primary objective of
    obtaining the package version. If there are multiple packages within the package,
    the highest version number found will be returned in the 'version' variable.
    """

    input_variables = {
        "source_pkg": {
            "required": True,
            "description": "The path of the package to interrogate.",
        },
    }
    output_variables = {
        "infodict": {"description": "A dictionary of information from the package.",},
        "version": {
            "description": "The version of the inputted package. Note that this will "
            "return the highest version found if multiple packages are found.",
        },
    }

    description = __doc__

    def parsePkgRefs(self, filename, path_to_pkg=None):
        """Parses a .dist or PackageInfo file looking for pkg-ref or pkg-info tags
        to get info on included sub-packages"""
        info = []
        dom = minidom.parse(filename)
        pkgrefs = dom.getElementsByTagName("pkg-info")
        if pkgrefs:
            # this is a PackageInfo file
            for ref in pkgrefs:
                keys = list(ref.attributes.keys())
                if "identifier" in keys and "version" in keys:
                    pkginfo = {}
                    pkginfo["packageid"] = ref.attributes["identifier"].value
                    pkginfo["version"] = ref.attributes["version"].value
                    payloads = ref.getElementsByTagName("payload")
                    if payloads:
                        keys = list(payloads[0].attributes.keys())
                        if "installKBytes" in keys:
                            pkginfo["installed_size"] = int(
                                float(payloads[0].attributes["installKBytes"].value)
                            )
                        if pkginfo not in info:
                            info.append(pkginfo)
                    # if there isn't a payload, no receipt is left by a flat
                    # pkg, so don't add this to the info array
        else:
            pkgrefs = dom.getElementsByTagName("pkg-ref")
            if pkgrefs:
                # this is a Distribution or .dist file
                pkgref_dict = {}
                for ref in pkgrefs:
                    keys = list(ref.attributes.keys())
                    if "id" in keys:
                        pkgid = ref.attributes["id"].value
                        if not pkgid in pkgref_dict:
                            pkgref_dict[pkgid] = {"packageid": pkgid}
                        if "version" in keys:
                            pkgref_dict[pkgid]["version"] = ref.attributes[
                                "version"
                            ].value
                        if "installKBytes" in keys:
                            pkgref_dict[pkgid]["installed_size"] = int(
                                float(ref.attributes["installKBytes"].value)
                            )
                        if ref.firstChild:
                            text = ref.firstChild.wholeText
                            if text.endswith(".pkg"):
                                if text.startswith("file:"):
                                    relativepath = unquote(text[5:])
                                    pkgdir = os.path.dirname(path_to_pkg or filename)
                                    pkgref_dict[pkgid]["file"] = os.path.join(
                                        pkgdir, relativepath
                                    )
                                else:
                                    if text.startswith("#"):
                                        text = text[1:]
                                    relativepath = unquote(text)
                                    thisdir = os.path.dirname(filename)
                                    pkgref_dict[pkgid]["file"] = os.path.join(
                                        thisdir, relativepath
                                    )

                for key in pkgref_dict:
                    pkgref = pkgref_dict[key]
                    if "file" in pkgref:
                        if os.path.exists(pkgref["file"]):
                            info.extend(self.getReceiptInfo(pkgref["file"]))
                            continue
                    if "version" in pkgref:
                        if "file" in pkgref:
                            del pkgref["file"]
                        info.append(pkgref_dict[key])

        return info

    def getReceiptInfo(self, pkgname):
        """Get receipt info from a package"""
        info = []
        if self.hasValidPackageExt(pkgname):
            self.output(f"Examining {pkgname}")
            if os.path.isfile(pkgname):  # new flat package
                info = self.getFlatPackageInfo(pkgname)

            if os.path.isdir(pkgname):  # bundle-style package?
                info = self.getBundlePackageInfo(pkgname)

        elif pkgname.endswith(".dist"):
            info = self.parsePkgRefs(pkgname)

        return info

    def getFlatPackageInfo(self, pkgpath):
        """
        returns array of dictionaries with info on subpackages
        contained in the flat package
        """

        infoarray = []
        # get the absolute path to the pkg because we need to do a chdir later
        abspkgpath = os.path.abspath(pkgpath)
        # make a tmp dir to expand the flat package into
        pkgtmp = tempfile.mkdtemp(dir="/tmp")
        # record our current working dir
        cwd = os.getcwd()
        # change into our tmp dir so we can use xar to unarchive the flat package
        os.chdir(pkgtmp)
        # Get the TOC of the flat pkg so we can search it later
        cmd_toc = ["/usr/bin/xar", "-tf", abspkgpath]
        proc = subprocess.Popen(
            cmd_toc, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        (toc, err) = proc.communicate()
        toc = toc.decode("UTF-8").strip().split("\n")
        if proc.returncode == 0:
            # Walk trough the TOC entries
            for toc_entry in toc:
                # If the TOC entry is a top-level PackageInfo, extract it
                if toc_entry.startswith("PackageInfo") and not infoarray:
                    cmd_extract = ["/usr/bin/xar", "-xf", abspkgpath, toc_entry]
                    result = subprocess.call(cmd_extract)
                    if result == 0:
                        packageinfoabspath = os.path.abspath(
                            os.path.join(pkgtmp, toc_entry)
                        )
                        infoarray = self.parsePkgRefs(packageinfoabspath)
                        break
                    else:
                        self.output(
                            f"An error occurred while extracting {toc_entry}: {err}"
                        )
                # If there are PackageInfo files elsewhere, gather them up
                elif toc_entry.endswith(".pkg/PackageInfo"):
                    cmd_extract = ["/usr/bin/xar", "-xf", abspkgpath, toc_entry]
                    result = subprocess.call(cmd_extract)
                    if result == 0:
                        packageinfoabspath = os.path.abspath(
                            os.path.join(pkgtmp, toc_entry)
                        )
                        infoarray.extend(self.parsePkgRefs(packageinfoabspath))
                    else:
                        self.output(
                            f"An error occurred while extracting {toc_entry}: {err}"
                        )
            if not infoarray:
                for toc_entry in [
                    item for item in toc if item.startswith("Distribution")
                ]:
                    # Extract the Distribution file
                    cmd_extract = ["/usr/bin/xar", "-xf", abspkgpath, toc_entry]
                    result = subprocess.call(cmd_extract)
                    if result == 0:
                        distributionabspath = os.path.abspath(
                            os.path.join(pkgtmp, toc_entry)
                        )
                        infoarray = self.parsePkgRefs(
                            distributionabspath, path_to_pkg=pkgpath
                        )
                        break
                    else:
                        self.output(
                            f"An error occurred while extracting {toc_entry}: {err}"
                        )

            if not infoarray:
                self.output("No valid Distribution or PackageInfo found.")
        else:
            self.output(err.decode("UTF-8"))

        # change back to original working dir
        os.chdir(cwd)
        shutil.rmtree(pkgtmp)
        return infoarray

    def getBomList(self, pkgpath):
        """Gets bom listing from pkgpath, which should be a path
        to a bundle-style package"""
        bompath = None
        for item in os.listdir(os.path.join(pkgpath, "Contents")):
            if item.endswith(".bom"):
                bompath = os.path.join(pkgpath, "Contents", item)
                break
        if not bompath:
            for item in os.listdir(os.path.join(pkgpath, "Contents", "Resources")):
                if item.endswith(".bom"):
                    bompath = os.path.join(pkgpath, "Contents", "Resources", item)
                    break
        if bompath:
            proc = subprocess.Popen(
                ["/usr/bin/lsbom", "-s", bompath],
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            output = proc.communicate()[0].decode("UTF-8")
            if proc.returncode == 0:
                return output.splitlines()
        return []

    def getOnePackageInfo(self, pkgpath):
        """Gets receipt info for a single bundle-style package"""
        pkginfo = {}
        plist = self.getBundleInfo(pkgpath)
        if plist:
            pkginfo["filename"] = os.path.basename(pkgpath)
            try:
                if "CFBundleIdentifier" in plist:
                    pkginfo["packageid"] = plist["CFBundleIdentifier"]
                elif "Bundle identifier" in plist:
                    # special case for JAMF Composer generated packages.
                    pkginfo["packageid"] = plist["Bundle identifier"]
                else:
                    pkginfo["packageid"] = os.path.basename(pkgpath)

                if "CFBundleName" in plist:
                    pkginfo["name"] = plist["CFBundleName"]

                if "IFPkgFlagInstalledSize" in plist:
                    pkginfo["installed_size"] = int(plist["IFPkgFlagInstalledSize"])

                pkginfo["version"] = self.getBundleVersion(pkgpath)
            except AttributeError:
                pkginfo["packageid"] = f"BAD PLIST in {os.path.basename(pkgpath)}"
                pkginfo["version"] = "0.0"
            ## now look for applications to suggest for blocking_applications
            # bomlist = getBomList(pkgpath)
            # if bomlist:
            #    pkginfo['apps'] = [os.path.basename(item) for item in bomlist
            #                        if item.endswith('.app')]

        else:
            # look for old-style .info files!
            infopath = os.path.join(pkgpath, "Contents", "Resources", "English.lproj")
            if os.path.exists(infopath):
                for item in os.listdir(infopath):
                    if os.path.join(infopath, item).endswith(".info"):
                        pkginfo["filename"] = os.path.basename(pkgpath)
                        pkginfo["packageid"] = os.path.basename(pkgpath)
                        infofile = os.path.join(infopath, item)
                        infodict = self.parseInfoFile(infofile)
                        pkginfo["version"] = infodict.get("Version", "0.0")
                        pkginfo["name"] = infodict.get("Title", "UNKNOWN")
                        break
        return pkginfo

    def getBundleInfo(self, path):
        """
        Returns Info.plist data if available
        for bundle at path
        """
        infopath = os.path.join(path, "Contents", "Info.plist")
        if not os.path.exists(infopath):
            infopath = os.path.join(path, "Resources", "Info.plist")

        if os.path.exists(infopath):
            try:
                plist = plistlib.readPlist(infopath)
                return plist
            except:  # TODO correct error
                pass

        return None

    def getBundlePackageInfo(self, pkgpath):
        """Get metadata from a bundle-style package"""
        infoarray = []

        if pkgpath.endswith(".pkg"):
            pkginfo = self.getOnePackageInfo(pkgpath)
            if pkginfo:
                infoarray.append(pkginfo)
                return infoarray

        bundlecontents = os.path.join(pkgpath, "Contents")
        if os.path.exists(bundlecontents):
            for item in os.listdir(bundlecontents):
                if item.endswith(".dist"):
                    filename = os.path.join(bundlecontents, item)
                    # return info using the distribution file
                    return self.parsePkgRefs(filename, path_to_pkg=bundlecontents)

            # no .dist file found, look for packages in subdirs
            dirsToSearch = []
            plist = self.getBundleInfo(pkgpath)
            if plist:
                if "IFPkgFlagComponentDirectory" in plist:
                    componentdir = plist["IFPkgFlagComponentDirectory"]
                    dirsToSearch.append(componentdir)

            if dirsToSearch == []:
                dirsToSearch = [
                    "",
                    "Contents",
                    "Contents/Installers",
                    "Contents/Packages",
                    "Contents/Resources",
                    "Contents/Resources/Packages",
                ]
            for subdir in dirsToSearch:
                searchdir = os.path.join(pkgpath, subdir)
                if os.path.exists(searchdir):
                    for item in os.listdir(searchdir):
                        itempath = os.path.join(searchdir, item)
                        if os.path.isdir(itempath):
                            if itempath.endswith(".pkg"):
                                pkginfo = self.getOnePackageInfo(itempath)
                                if pkginfo:
                                    infoarray.append(pkginfo)
                            elif itempath.endswith(".mpkg"):
                                pkginfo = self.getBundlePackageInfo(itempath)
                                if pkginfo:
                                    infoarray.extend(pkginfo)

        return infoarray

    def hasValidPackageExt(self, path):
        """Verifies a path ends in '.pkg' or '.mpkg'"""
        ext = os.path.splitext(path)[1]
        return ext.lower() in [".pkg", ".mpkg"]

    def getPkgRestartInfo(self, filename):
        """Uses Apple's installer tool to get RestartAction
        from an installer item."""
        installerinfo = {}
        proc = subprocess.Popen(
            ["/usr/sbin/installer", "-query", "RestartAction", "-pkg", filename],
            bufsize=-1,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        (out, err) = proc.communicate()
        out = out.decode("UTF-8")
        err = err.decode("UTF-8")
        if proc.returncode:
            self.output(f"installer -query failed: {out} {err}")
            return {}

        if out:
            restartAction = out.rstrip("\n")
            if restartAction != "None":
                installerinfo["RestartAction"] = restartAction

        return installerinfo

    def nameAndVersion(self, aString):
        """
        Splits a string into the name and version numbers:
        'TextWrangler2.3b1' becomes ('TextWrangler', '2.3b1')
        'AdobePhotoshopCS3-11.2.1' becomes ('AdobePhotoshopCS3', '11.2.1')
        'MicrosoftOffice2008v12.2.1' becomes ('MicrosoftOffice2008', '12.2.1')
        """
        # first try regex
        m = re.search(r"[0-9]+(\.[0-9]+)((\.|a|b|d|v)[0-9]+)+", aString)
        if m:
            vers = m.group(0)
            name = aString[0 : aString.find(vers)].rstrip(" .-_v")
            return (name, vers)

        # try another way
        index = 0
        for char in aString[::-1]:
            if char in "0123456789._":
                index -= 1
            elif char in "abdv":
                partialVersion = aString[index:]
                if set(partialVersion).intersection(set("abdv")):
                    # only one of 'abdv' allowed in the version
                    break
                else:
                    index -= 1
            else:
                break

        if index < 0:
            possibleVersion = aString[index:]
            # now check from the front of the possible version until we
            # reach a digit (because we might have characters in '._abdv'
            # at the start)
            for char in possibleVersion:
                if not char in "0123456789":
                    index += 1
                else:
                    break
            vers = aString[index:]
            return (aString[0:index].rstrip(" .-_v"), vers)
        # no version number found,
        # just return original string and empty string
        return (aString, "")

    def getBundleVersion(self, bundlepath, key=None):
        """
        Returns version number from a bundle.
        Some extra code to deal with very old-style bundle packages
        Specify key to use a specific key in the Info.plist for
        the version string.
        """
        plist = self.getBundleInfo(bundlepath)
        if plist:
            versionstring = self.getVersionString(plist, key)
            if versionstring:
                return versionstring

        # no version number in Info.plist. Maybe old-style package?
        infopath = os.path.join(bundlepath, "Contents", "Resources", "English.lproj")
        if os.path.exists(infopath):
            for item in os.listdir(infopath):
                if os.path.join(infopath, item).endswith(".info"):
                    infofile = os.path.join(infopath, item)
                    infodict = self.parseInfoFile(infofile)
                    return infodict.get("Version", "0.0.0.0.0")

        # didn't find a version number, so return 0...
        return "0.0.0.0.0"

    def getPackageMetaData(self, pkgitem):
        """
        Queries an installer item (.pkg, .mpkg, .dist)
        and gets metadata. There are a lot of valid Apple package formats
        and this function may not deal with them all equally well.
        Standard bundle packages are probably the best understood and documented,
        so this code deals with those pretty well.
        metadata items include:
        installer_item_size:  size of the installer item (.dmg, .pkg, etc)
        installed_size: size of items that will be installed
        RestartAction: will a restart be needed after installation?
        name
        version
        description
        receipts: an array of packageids that may be installed
                (some may not be installed on some machines)
        """

        if not self.hasValidPackageExt(pkgitem):
            return {}

        # first query /usr/sbin/installer for restartAction
        installerinfo = self.getPkgRestartInfo(pkgitem)
        # now look for receipt/subpkg info
        receiptinfo = self.getReceiptInfo(pkgitem)

        name = os.path.split(pkgitem)[1]
        shortname = os.path.splitext(name)[0]
        metaversion = self.getBundleVersion(pkgitem)
        if metaversion == "0.0.0.0.0":
            metaversion = self.nameAndVersion(shortname)[1]

        highestpkgversion = "0.0"
        installedsize = 0
        for infoitem in receiptinfo:
            if APLooseVersion(infoitem["version"]) > APLooseVersion(highestpkgversion):
                highestpkgversion = infoitem["version"]
            if "installed_size" in infoitem:
                # note this is in KBytes
                installedsize += infoitem["installed_size"]

        if metaversion == "0.0.0.0.0":
            metaversion = highestpkgversion
        elif len(receiptinfo) == 1:
            # there is only one package in this item
            metaversion = highestpkgversion
        elif highestpkgversion.startswith(metaversion):
            # for example, highestpkgversion is 2.0.3124.0,
            # version in filename is 2.0
            metaversion = highestpkgversion

        cataloginfo = {}
        cataloginfo["name"] = self.nameAndVersion(shortname)[0]
        cataloginfo["version"] = metaversion
        for key in ("display_name", "RestartAction", "description"):
            if key in installerinfo:
                cataloginfo[key] = installerinfo[key]

        if "installed_size" in installerinfo:
            if installerinfo["installed_size"] > 0:
                cataloginfo["installed_size"] = installerinfo["installed_size"]
        elif installedsize:
            cataloginfo["installed_size"] = installedsize

        cataloginfo["receipts"] = receiptinfo

        if os.path.isfile(pkgitem) and not pkgitem.endswith(".dist"):
            # flat packages require 10.5.0+
            cataloginfo["minimum_os_version"] = "10.5.0"

        return cataloginfo

    def main(self):
        """Do the thing"""
        # Check if we're trying to copy something inside a dmg.
        (dmg_path, dmg, dmg_source_path) = self.parsePathForDMG(self.env["source_pkg"])
        try:
            if dmg:
                # Mount dmg and copy path inside.
                mount_point = self.mount(dmg_path)
                source_pkg = os.path.join(mount_point, dmg_source_path)
            else:
                # Straight copy from file system.
                source_pkg = self.env["source_pkg"]

            # Process the path for globs
            matches = glob.glob(source_pkg)
            matched_source_path = matches[0]
            if len(matches) > 1:
                self.output(
                    f"WARNING: Multiple paths match 'source_pkg' glob '{source_pkg}':"
                )
                for match in matches:
                    self.output(f"  - {match}")

            if [c for c in "*?[]!" if c in source_pkg]:
                self.output(
                    f"Using path '{matched_source_path}' matched from globbed "
                    f"'{source_pkg}'."
                )

            infodict = self.getPackageMetaData(matched_source_path)
            self.env["infodict"] = infodict
            self.env["version"] = infodict["version"]

        finally:
            if dmg:
                self.unmount(dmg_path)


if __name__ == "__main__":
    PROCESSOR = Copier()
    PROCESSOR.execute_shell()
