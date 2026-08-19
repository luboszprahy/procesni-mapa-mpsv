# solution pack

Package solution components on local filesystem into solution.zip (SolutionPackager).

## Arguments

- `--zipfile` (`-z`) - The full path to the solution ZIP file
- `--folder` (`-f`) - The path to the root folder on the local filesystem. When unpacking or extracting, this is written to. When packing this is read from.
- `--packagetype` (`-p`) - When unpacking or extracting, use to specify dual Managed and Unmanaged operation. When packing, use to specify Managed or Unmanaged from a previous unpack 'Both'. Can be: 'Unmanaged', 'Managed' or 'Both'. The default value is 'Unmanaged'.
- `--log` (`-l`) - The path to the log file.
- `--errorlevel` (`-e`) - Minimum logging level for log output [Verbose|Info|Warning|Error|Off]. The default value is 'Info'.
- `--singleComponent` (`-sc`) - Only perform action on a single component type [WebResource|Plugin|Workflow|None]. The default value is 'None'.
- `--allowDelete` (`-ad`) - Dictates if delete operations may occur. The default value is 'false'.
- `--allowWrite` (`-aw`) - Dictates if write operations may occur. The default value is 'false'.
- `--clobber` (`-c`) - Enables that files marked read-only can be deleted or overwritten. The default value is 'false'.
- `--map` (`-m`) - The full path to a mapping xml file from which to read component folders to pack.
- `--sourceLoc` (`-src`) - Generates a template resource file. Valid only on extract. Possible values are 'auto', or language code of the language you wish to export. You can use Language Code Identifier (LCID), or International Organization for Standardization (ISO) language code formats. When present, this extracts the string resources from the given locale as a neutral .resx. If 'auto' or just the long or short form of the switch is specified, the base locale for the solution is used.
- `--localize` (`-loc`) - Extract or merge all string resources into .resx files.
- `--useLcid` (`-lcid`) - Use Language Code Identifier (LCID) values (1033) rather than International Organization for Standardization (ISO) codes (en-US) for language files.
- `--useUnmanagedFileForMissingManaged` (`-same`) - Use the same XML source file when packaging for Managed and only Unmanaged XML file is found; applies to AppModuleSiteMap, AppModuleMap, FormXml files.
- `--disablePluginRemap` (`-dpm`) - Disabled plug-in fully qualified type name remapping. The default value is 'false'.

