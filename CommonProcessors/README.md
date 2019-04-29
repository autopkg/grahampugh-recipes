# Common Processors

To use these processors, add the processor as so:

    com.github.grahampugh.recipes.commonprocessors/NameOfProcessor

## SubDirectoryList

This processor is originally from Jesse Peterson. A newer version is currently at [https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py](https://github.com/facebook/Recipes-for-AutoPkg/blob/master/Shared_Processors/SubDirectoryList.py).

It is used to generate a list of all folders in a path. That list is then processed by other procesors such as `LocalRepoUpdateChecker`.
