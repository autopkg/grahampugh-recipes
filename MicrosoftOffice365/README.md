# Microsoft Office 365

This recipe downloads the latest Microsoft Office 365 SKU-less installer package. This is also valid for Office 2019, since the installers are the same. These are the full installer packages, not the update-only packages.

The recipe can also be used to download Microsoft Office 2016 or Office 365 Business Pro editions by overriding the `PRODUCTID` key.

Override the `PRODUCTID` key as follows:

- `525133` for Office 365 (Americas)
- `532572` for Office 365 (Europe) (this is set by default)
- `532577` for Office 365 (Asia)
- `2009112` for Office 365 Business Pro (Americas) (includes Teams) 
- `871743` for Office 2016
