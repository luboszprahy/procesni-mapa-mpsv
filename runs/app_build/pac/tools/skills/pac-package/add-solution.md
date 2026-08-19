# package add-solution

Adds a prebuilt Dataverse solution file to a Package Deployer Package project.

## Arguments

- `--path` (`-p`) - Path to the Dataverse solution file. The file must be a compressed ZIP file.
- `--import-order` - A whole number that indicates the order to insert this item into the final ImportConfig.xml file at build time. Negative numbers are inserted before existing elements. Positive numbers are added after existing elements.
- `--skip-validation` (`-sv`) - Adds the item to the project file even if the file doesn't exist or appears to be invalid. Note: Using this doesn't affect any validation performed by MSBuild.
- `--publish-workflows-activate-plugins` - Explicitly indicates whether to publish the workflows and activate plug-ins when this solution is imported.
- `--overwrite-unmanaged-customizations` - Explicitly indicates whether to overwrite unmanaged customizations when this solution is imported.
- `--import-mode` - Explicitly specifies the required mode when importing this solution.
- `--missing-dependency-behavior` - Specifies the behavior on import when a dependency of this solution is missing from the target environment.
- `--dependency-overrides` - A semicolon delimited list of overrides. This value overrides any dependency information encoded in the solution's metadata. Each override should be in the format: `<uniquename>:<minVersion>:<maxVersion>`. Where minVersion and maxVersion are optional but should be in .NET version format syntax.

