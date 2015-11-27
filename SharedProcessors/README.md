# MunkiGitBranchingCommitter
Example use:
```
$ autopkg run GoogleChrome.munki.recipe --post com.github.grahampugh.shared/MunkiGitBranchingCommitter
```
This will add and commit the pkginfo to your git repository with the message format:
```
[AutoPkg] Adding %NAME% version %VERSION%
```
This will be pushed to a new branch, named `autopkg_run_<timestamp>`
