# grahampugh-recipes

A few recipes not found elsewhere. To use them, enter the following command:

    autopkg repo-add grahampugh/recipes-yaml

Note that some recipes in this repo are designed to help package up software that is not publicly available. As such, those recipes have no `.download` recipe. Those recipes have their own `README` files to give further instruction.

## Wait, these are all yaml files!

I write my recipes as `yaml` files, and then convert them to `plist` format when I'm done. I find constructing the recipes much nicer in `yaml` format, and it ensures a consistent `plist` structure (e.g. alphabetised input keys).

If, on the other hand, you are interested in this technique, take a look at https://github.com/grahampugh/plist-yaml-plist

## JamfUploader processors

This repo contains a "stable" copy of the `JamfUploader` processors, used for uploading packages and other objects to Jamf Pro using the API. The original and latest version of these processors is in the repo [grahampugh/jamf-upload](https://github.com/grahampugh/jamf-upload). 

For details on how to use the `JamfUploader` processors, please consult the [JamfUploader Wiki](https://github.com/grahampugh/jamf-upload/wiki).

Note that if you wish to use the latest version of the `JamfUploader` processors, you can still have this repo in your AutoPkg Recipe List as well as the `jamf-upload` repo. You just have to make sure that `grahampugh/jamf-upload` is ABOVE `autopkg/grahampugh-recipes` in the recipe search list. To achieve this, you can run the following commands in this order:

    autopkg repo-delete grahampugh-recipes
    autopkg repo-add grahampugh/jamf-upload
    autopkg repo-add grahampugh-recipes
