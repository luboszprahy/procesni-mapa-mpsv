# solution sync

Sync the current Dataverse solution project to the current state of the solution in your organization.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--solution-folder` (`-f`) - Path to the local, unpacked solution folder: either the root of the 'Other/Solution.xml' file or a folder with a .cdsproj file.
- `--include` (`-i`) - Which settings should be included in the solution being exported.
- `--async` (`-a`) - Exports the solution asynchronously.
- `--max-async-wait-time` (`-wt`) - Max asynchronous wait time in minutes. The default value is 60 minutes.
- `--packagetype` (`-p`) - When unpacking or extracting, use to specify dual Managed and Unmanaged operation. When packing, use to specify Managed or Unmanaged from a previous unpack 'Both'. Can be: 'Unmanaged', 'Managed' or 'Both'. The default value is: 'Both'.
- `--localize` (`-loc`) - Extract or merge all string resources into .resx files.
- `--map` (`-m`) - The full path to a mapping xml file from which to read component folders to pack.

