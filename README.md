# grahampugh-recipes

A few recipes not found elsewhere. To use them, enter the following command:

    autopkg repo-add grahampugh-recipes

Note that some recipes in this repo are designed to help package up software that is not publicly available. As such, those recipes have no `.download` recipe. Those recipes have their own `README` files to give further instruction.


## What is the YAML folder?

I write my recipes as `yaml` files, and then convert them to `plist` format when I'm done. I find constructing the recipes much nicer in `yaml` format, and it ensures a consistent `plist` structure (e.g. alphabetised input keys).

You can safely ignore the contents of the `YAML` folder if you wish. If, on the other hand, you are interested in this technique, take a look at https://github.com/grahampugh/plist-yaml-plist
