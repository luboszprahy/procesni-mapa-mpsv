# copilot merge-translation

Merge files containing localized content for one or more bots.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--sourcedir` (`-src`) - Source solution directory. When specified, will ignore the connected environment when looking for bots and instead look for content in the solution folder.
- `--file` (`-f`) - The list of files that contain translations. Glob patterns are supported.
- `--whatif` - Does not execute the command, but outputs the details of what would happen.
- `--verbose` - Output more diagnostic information during data import/export
- `--solution` (`-s`) - Name of the solution.

