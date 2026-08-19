# pages migrate-datamodel

Manage data model migration for your Power Pages website.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--webSiteId` (`-id`) - Power Pages website ID to update the site.
- `--mode` (`-m`) - Choose from configurationData / configurationDataReferences / all - based on your requirement.
- `--siteCustomizationReportPath` (`-p`) - Local path to store the site customization report.
- `--checkMigrationStatus` (`-s`) - To check the status of the site with migration in progress.
- `--updateDataModelVersion` (`-u`) - Update data model version for the site once the data is migrated successfully.
- `--revertToStandardDataModel` (`-r`) - Revert site from enhanced to standard data model.
- `--resetMigration` (`-rs`) - Resets the data model migration process.
- `--portalId` (`-pid`) - Portal ID for the website under migration.
- `--verbose` (`-v`) - Enables verbose mode to provide more details during data model migration.

