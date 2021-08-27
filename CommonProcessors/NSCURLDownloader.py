#!/usr/local/autopkg/python
#
# Refactoring 2018 Michal Moravec
# Copyright 2015 Greg Neagle
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
"""See docstring for NSCURLDownloader class"""

import os.path
import tempfile
import subprocess

from autopkglib import BUNDLE_ID, Processor, ProcessorError, xattr

__all__ = ["NSCURLDownloader"]


class NSCURLDownloader(Processor):
    """Downloads a URL to the specified download_dir using nscurl."""

    description = __doc__
    input_variables = {
        "url": {"required": True, "description": "The URL to download."},
        "download_dir": {
            "required": False,
            "description": (
                "The directory where the file will be downloaded to. Defaults "
                "to RECIPE_CACHE_DIR/downloads."
            ),
        },
        "filename": {
            "required": False,
            "description": "Filename to override the URL's tail.",
        },
        "CHECK_FILESIZE_ONLY": {
            "default": False,
            "required": False,
            "description": (
                "If True, a server's ETag and Last-Modified "
                "headers will not be checked to verify whether "
                "a download is newer than a cached item, and only "
                "Content-Length (filesize) will be used. This "
                "is useful for cases where a download always "
                "redirects to different mirrors, which could "
                "cause items to be needlessly re-downloaded. "
                "Defaults to False."
            ),
        },
        "PKG": {
            "required": False,
            "description": (
                "Local path to the pkg/dmg we'd otherwise download. "
                "If provided, the download is skipped and we just use "
                "this package or disk image."
            ),
        },
    }
    output_variables = {
        "pathname": {"description": "Path to the downloaded file."},
        "last_modified": {
            "description": "last-modified header for the downloaded item."
        },
        "etag": {"description": "etag header for the downloaded item."},
        "download_changed": {
            "description": (
                "Boolean indicating if the download has changed since the "
                "last time it was downloaded."
            )
        },
        "nscurl_downloader_summary_result": {
            "description": "Description of interesting results."
        },
    }

    def download_with_nscurl(self, url, pathname_temporary):
        """
        build an nscurl command based on method (GET, PUT, POST, DELETE)
        If the URL contains 'uapi' then token should be passed to the auth variable,
        otherwise the enc_creds variable should be passed to the auth variable
        """
        headers_file = "/tmp/nscurl_headers_from_autopkg.txt"

        # build the nscurl command
        nscurl_cmd = [
            "/usr/bin/nscurl",
            "-D",
            headers_file,
            "--output",
            pathname_temporary,
            url,
            "-v",
        ]

        self.output(f"\nnscurl command:\n{' '.join(nscurl_cmd)}", verbose_level=2)

        # now subprocess the nscurl command and build the r tuple which contains the
        # headers, status code and outputted data
        subprocess.check_output(nscurl_cmd)

        try:
            with open(headers_file, "r") as file:
                headers = file.readlines()
            r = [x.strip() for x in headers]
            return r
        except IOError:
            print("WARNING: {} not found".format(headers_file))

    def getxattr(self, attr):
        """Get a named xattr from a file. Return None if not present."""

        if attr in xattr.listxattr(self.env["pathname"]):
            return xattr.getxattr(self.env["pathname"], attr).decode()
        return None

    def clear_zero_file(self, pathname):
        """If file already exists and the size is 0, discard it to download again."""
        if os.path.exists(pathname) and os.path.getsize(pathname) == 0:
            os.remove(pathname)

    def clear_vars(self):
        """Clear and initialize variables."""
        # Delete summary result if exists
        if "nsurl_downloader_summary_result" in self.env:
            del self.env["nsurl_downloader_summary_result"]

        # XATTR names for Etag and Last-Modified headers
        self.xattr_etag = f"{BUNDLE_ID}.etag"
        self.xattr_last_modified = f"{BUNDLE_ID}.last-modified"

        self.env["last_modified"] = ""
        self.env["etag"] = ""
        self.existing_file_size = None

    def get_filename(self):
        """Obtain filename from PKG variable or URL."""
        if "PKG" in self.env:
            self.env["pathname"] = os.path.expanduser(self.env["PKG"])
            self.env["download_changed"] = True
            self.output(f"Given {self.env['pathname']}, no download needed.")
            return None

        if "filename" in self.env:
            filename = self.env["filename"]
        else:
            # Generate filename from URL.
            filename = self.env["url"].rpartition("/")[2]

        return filename

    def get_download_dir(self):
        """Create download dir and return its path."""
        download_dir = self.env.get("download_dir") or os.path.join(
            self.env["RECIPE_CACHE_DIR"], "downloads"
        )
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except OSError as err:
                raise ProcessorError(f"Can't create {download_dir}: {err.strerror}")
        return download_dir

    def create_temp_file(self, download_dir):
        """Create temporary file and return its path."""
        temporary_file = tempfile.NamedTemporaryFile(dir=download_dir, delete=False)
        pathname_temporary = temporary_file.name
        # Set permissions on the temp file as curl would set for a newly-downloaded
        # file. NamedTemporaryFile uses mkstemp(), which sets a mode of 0600, and
        # this can cause issues if this item is eventually copied to a Munki repo
        # with the same permissions and the file is inaccessible by (for example)
        # the webserver.
        os.chmod(pathname_temporary, 0o644)
        return pathname_temporary

    def download_changed(self, header):
        """Check if downloaded file changed on server."""
        # If Content-Length header is present and we had a cached
        # file, see if it matches the size of the cached file.
        # Useful for webservers that don't provide Last-Modified
        # and ETag headers.
        if (not header.get("etag") and not header.get("last-modified")) or self.env[
            "CHECK_FILESIZE_ONLY"
        ]:
            size_header = header.get("content-length")
            if size_header and int(size_header) == self.existing_file_size:
                self.env["download_changed"] = False
                self.output(
                    "File size returned by webserver matches that "
                    f"of the cached file: {size_header} bytes"
                )
                self.output(
                    "WARNING: Matching a download by filesize is a "
                    "fallback mechanism that does not guarantee "
                    "that a build is unchanged."
                )
                self.output(f"Using existing {self.env['pathname']}")
                return False

        if header["http_result_code"] == "304":
            # resource not modified
            self.env["download_changed"] = False
            self.output("Item at URL is unchanged.")
            self.output(f"Using existing {self.env['pathname']}")
            return False

        return True

    def move_temp_file(self, pathname_temporary):
        """Move temporary download file to pathname."""
        if os.path.exists(self.env["pathname"]):
            os.remove(self.env["pathname"])
        try:
            os.rename(pathname_temporary, self.env["pathname"])
        except OSError:
            raise ProcessorError(
                f"Can't move {pathname_temporary} to {self.env['pathname']}"
            )

    def store_headers(self, header):
        """Store last-modified and etag headers in pathname xattr."""
        if header.get("last-modified"):
            self.env["last_modified"] = header.get("last-modified")
            xattr.setxattr(
                self.env["pathname"],
                self.xattr_last_modified,
                header.get("last-modified").encode(),
            )
            self.output(
                f"Storing new Last-Modified header: {header.get('last-modified')}"
            )

        self.env["etag"] = ""
        if header.get("etag"):
            self.env["etag"] = header.get("etag")
            xattr.setxattr(
                self.env["pathname"], self.xattr_etag, header.get("etag").encode()
            )
            self.output(f"Storing new ETag header: {header.get('etag')}")

    def clear_header(self, header):
        """Clear header dictionary."""
        # Save redirect URL before clear
        http_redirected = header.get("http_redirected", None)
        header.clear()
        header["http_result_code"] = "000"
        header["http_result_description"] = ""
        # Restore redirect URL
        header["http_redirected"] = http_redirected

    def parse_http_protocol(self, line, header):
        """Parse first HTTP header line."""
        try:
            header["http_result_code"] = line.split(None, 2)[1]
            header["http_result_description"] = line.split(None, 2)[2]
        except IndexError:
            pass

    def parse_http_header(self, line, header):
        """Parse single HTTP header line."""
        part = line.split(None, 1)
        fieldname = part[0].rstrip(":").lower()
        try:
            header[fieldname] = part[1]
        except IndexError:
            header[fieldname] = ""

    def parse_headers(self, raw_headers):
        """Parse headers from nscurl."""
        header = {}
        self.clear_header(header)
        for line in raw_headers:
            if line.startswith("HTTP/"):
                self.parse_http_protocol(line, header)
            elif ": " in line:
                self.parse_http_header(line, header)
            elif line == "":
                # we got an empty line; end of headers (or curl exited)
                if header.get("http_result_code") in [
                    "301",
                    "302",
                    "303",
                    "307",
                    "308",
                ]:
                    # redirect, so more headers are coming.
                    # Throw away the headers we've received so far
                    header["http_redirected"] = header.get("location", None)
                    self.clear_header(header)
        return header

    def main(self):
        # Clear and initialize data structures
        self.clear_vars()

        # Ensure existence of necessary files, directories and paths
        filename = self.get_filename()
        if filename is None:
            return
        download_dir = self.get_download_dir()
        self.env["pathname"] = os.path.join(download_dir, filename)
        pathname_temporary = self.create_temp_file(download_dir)

        # Clear out a potentially zero-byte file
        self.clear_zero_file(self.env["pathname"])

        # Execute curl command and parse headers
        raw_headers = self.download_with_nscurl(self.env["url"], pathname_temporary)
        header = self.parse_headers(raw_headers)

        if self.download_changed(header):
            self.env["download_changed"] = True
        else:
            # Discard the temp file
            os.remove(pathname_temporary)
            return

        # New resource was downloaded. Move the temporary download file to the pathname
        self.move_temp_file(pathname_temporary)

        # Save last-modified and etag headers to files xattr
        self.store_headers(header)

        # Generate output messages and variables
        self.output(f"Downloaded {self.env['pathname']}")
        self.env["nscurl_downloader_summary_result"] = {
            "summary_text": "The following new items were downloaded:",
            "data": {"download_path": self.env["pathname"]},
        }


if __name__ == "__main__":
    PROCESSOR = NSCURLDownloader()
    PROCESSOR.execute_shell()
