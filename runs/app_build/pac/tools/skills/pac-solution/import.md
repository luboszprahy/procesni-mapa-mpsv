# solution import

Import the solution into Dataverse.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--path` (`-p`) - Path to solution zip file. If not specified, assumes the current folder is a cdsproj project.
- `--activate-plugins` (`-ap`) - Activate plug-ins and workflows on the solution.
- `--force-overwrite` (`-f`) - Force an overwrite of unmanaged customizations
- `--skip-dependency-check` (`-s`) - Skip dependency check against dependencies flagged as product update
- `--import-as-holding` (`-h`) - Import the solution as a holding solution.
- `--stage-and-upgrade` (`-up`) - Import and upgrade the solution.
- `--publish-changes` (`-pc`) - Publish your changes upon a successful import.
- `--async` (`-a`) - Imports the solution asynchronously.
- `--max-async-wait-time` (`-wt`) - Max asynchronous wait time in minutes. The default value is 60 minutes.
- `--settings-file` - The .json file with the deployment settings for connection references and environment variables.
- `--skip-lower-version` (`-slv`) - Skip solution import if same or higher version is present in current environment.

