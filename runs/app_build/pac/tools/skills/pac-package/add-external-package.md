# package add-external-package

Adds a package that is external to the Dataverse solution system to a Package Deployer Package project.

## Arguments

- `--path` (`-p`) - Path to the external package
- `--package-type` (`-t`) - The type of the package being added. For example: 'xpp' for FnO packages.
- `--import-order` - A whole number that indicates the order to insert this item into the final ImportConfig.xml file at build time. Negative numbers are inserted before existing elements. Positive numbers are added after existing elements.
- `--skip-validation` (`-sv`) - Adds the item to the project file even if the file doesn't exist or appears to be invalid. Note: Using this doesn't affect any validation performed by MSBuild.

