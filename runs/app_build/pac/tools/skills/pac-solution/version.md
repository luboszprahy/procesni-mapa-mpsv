# solution version

Update build or revision version for the solution.

## Arguments

- `--strategy` (`-s`) - Updates build version for 'Solution.xml' file using specified strategy. If using gittags, set personal access token in the following environment variable "PacCli.PAT"
- `--patchversion` (`-pv`) - Patch version for the solution.
- `--buildversion` (`-bv`) - Build version for the solution.
- `--revisionversion` (`-rv`) - Revision version for the solution.
- `--filename` (`-fn`) - Tracker CSV file name to be used when using filetracking as a strategy. The default value is 'ControlsStateVersionInfo.csv'.
- `--solutionPath` (`-sp`) - Path to Dataverse solution directory or Solution.xml file.

