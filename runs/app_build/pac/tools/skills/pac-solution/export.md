# solution export

Export a solution from Dataverse.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--name` (`-n`) - The name of the solution to be exported.
- `--path` (`-p`) - Path where the exported solution zip file is written.
- `--managed` (`-m`) - Whether the solution should be exported as a managed solution.
- `--targetversion` (`-v`) - The version that the exported solution will support
- `--include` (`-i`) - Which settings should be included in the solution being exported.
- `--async` (`-a`) - Exports the solution asynchronously.
- `--max-async-wait-time` (`-wt`) - Max asynchronous wait time in minutes. The default value is 60 minutes.
- `--overwrite` (`-ow`) - The exported solution file can overwrite the solution zip file on the local file system.

