# package deploy

Deploys package to Dataverse

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--logFile` (`-lf`) - Log file path
- `--logConsole` (`-c`) - Output log to console
- `--package` (`-p`) - Path to a package dll or zip file with a package.
- `--solution` (`-sz`) - Path to the Dataverse solution file. The file must be a compressed ZIP or CAB file.
- `--settings` (`-s`) - Runtime Package Settings that are passed to the package that is being deployed. The format of the string must be `key=value|key=value`.
- `--verbose` (`-vdbg`) - Emit verbose logs to the log outputs.
- `--package-type` (`-pt`) - Target platform for deployment. Allowed values: dataverse, erp. Default: dataverse.
- `--build-type` (`-bt`) - How the package is applied. Allowed values: Full, Incremental, Delete. Default: Full. Used with --package-type erp.
- `--release-type` (`-rt`) - Package classification. Allowed values: Dev, Release. Default: Dev. Release packages force a full database sync on the server. Used with --package-type erp.
- `--db-sync` (`-ds`) - Database synchronization mode to run after deploy. Allowed values: None, Full, Module, Incremental. Default: None. Used with --package-type erp.
- `--modules` (`-m`) - Comma-separated list of module names to synchronize. Required when --db-sync is Module.
- `--argument-file` (`-af`) - Path to a JSON file matching the IncrementalSyncParameters (or ModuleSyncParameters) contract. Required for --db-sync Incremental.
- `--solution-root` (`-sr`) - Solution-mode only: root folder containing .erp/xpp.json. Defaults to the current directory. When --package is omitted under --package-type erp, all models listed in .erp/xpp.json are deployed in dependency order.
- `--outputDirectory` (`-o`) - Solution-mode only: root folder containing .erp/xpp.json. Defaults to the current directory. When --package is omitted under --package-type erp, all models listed in .erp/xpp.json are deployed in dependency order.

