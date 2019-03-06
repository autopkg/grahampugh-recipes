# Common Processors

To use these processors, add the processor as so:

```
com.github.grahampugh.recipes.commonprocessors/NameOfProcessor
```

## LocalRepoUpdateChecker

This is used to determine the latest available update in a local repository.
It requires a folder for each version, with the folder name representing the version number. A DMG containing the installer should be within each folder. Python's `LooseVersion` is used to determine the latest version.

---

## SubDirectoryList

This processor is originally from Jesse Peterson. A newer version is currently at [https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py](https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py).

It is used to generate a list of all folders in a path. That list is then processed by other procesors such as `LocalRepoUpdateChecker`.

---

## SetIconForFileOrFolder

This processor is designed to add an `.icns` file to a folder. The use case is for applications that are installed inside a folder which has an icon.

(At the moment, this processor does not appear to work, although the icon is correctly copied).
