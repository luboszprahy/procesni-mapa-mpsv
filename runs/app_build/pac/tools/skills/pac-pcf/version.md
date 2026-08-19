# pcf version

Patch version for controls

## Arguments

- `--strategy` (`-s`) - Updates patch version for 'ControlManifest.xml' files using specified strategy. If using gittags, set a personal access token in the following environment variable "PacCli.PAT"
- `--patchversion` (`-pv`) - Patch version for controls
- `--path` (`-p`) - Absolute/Relative path of the 'ControlManifest.xml' for updating.
- `--allmanifests` (`-a`) - Updates patch version for all 'ControlManifest.xml' files
- `--updatetarget` (`-ut`) - Specify which target manifest needs to be updated.
- `--filename` (`-fn`) - Tracker CSV file name to be used when using filetracking as a strategy. The default value is 'ControlsStateVersionInfo.csv'.

