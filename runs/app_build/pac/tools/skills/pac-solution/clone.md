# solution clone

Create a solution project based on an existing solution in your organization.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--name` (`-n`) - The name of the solution to be exported.
- `--targetversion` (`-v`) - The version that the exported solution will support
- `--include` (`-i`) - Which settings should be included in the solution being exported.
- `--outputDirectory` (`-o`) - Output directory
- `--async` (`-a`) - Exports the solution asynchronously.
- `--max-async-wait-time` (`-wt`) - Max asynchronous wait time in minutes. The default value is 60 minutes.
- `--packagetype` (`-p`) - Specifies the extraction type for the solution. Can be: 'Unmanaged', 'Managed' or 'Both'. The default value is: 'Both'.
- `--localize` (`-loc`) - Extract or merge all string resources into .resx files.
- `--map` (`-m`) - The full path to a mapping xml file from which to read component folders to pack.

