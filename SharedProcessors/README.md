# MunkiGitCommitter
Example use:
```
$ autopkg run GoogleChrome.munki.recipe --post com.github.grahampugh.recipes.SharedProcessor/MunkiGitCommitter
```
This will add and commit the pkginfo to your git repository with the message format:
```
[AutoPkg] Adding %NAME% version %VERSION%
```
This will be pushed to the `master` branch.

For use with AutoPkgr, set the postprocessor as `com.github.grahampugh.recipes.SharedProcessor/MunkiGitCommitter`


# MunkiGitBranchingCommitter
Example use:
```
$ autopkg run GoogleChrome.munki.recipe --post com.github.grahampugh.recipes.SharedProcessor/MunkiGitBranchingCommitter
```
This will add and commit the pkginfo to your git repository with the message format:
```
[AutoPkg] Adding %NAME% version %VERSION%
```
This will be pushed to a new branch, named `autopkg_run_<timestamp>`.

For use with AutoPkgr, set the postprocessor as `com.github.grahampugh.recipes.SharedProcessor/MunkiGitBranchingCommitter`


# License
Both processors are adapted from `MunkiGitCommitter.py`, copyright 2015 Nathan Felton (n8felton).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and
limitations under the License.


