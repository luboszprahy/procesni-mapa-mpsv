# pcf push

Import the Power Apps component framework project into the current Dataverse organization

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--publisher-prefix` (`-pp`) - Customization prefix value for the Dataverse solution publisher
- `--solution-unique-name` - The unique name of the solution to add the component to.
- `--verbosity` (`-v`) - Verbosity level for MSBuild when building the temporary solution wrapper.
- `--force-import` (`-f`) - Force a full update of the control as part of a temporary solution
- `--interactive` (`-i`) - Indicates that actions in the build are allowed to interact with the user. Don't use this argument in an automated scenario where interactivity is not expected.
- `--incremental` (`-inc`) - Pushes only files which are different using entity updates.

