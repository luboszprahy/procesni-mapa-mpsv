# solution check

Upload a Dataverse solution project to run against the Power Apps Checker service.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--path` (`-p`) - Path where one or more solution files to be checked exist. The path can contain glob/wildcard characters.
- `--solutionUrl` (`-u`) - SAS Uri pointing to solution.zip to be analyzed
- `--outputDirectory` (`-o`) - Output directory
- `--geo` (`-g`) - Which geographical instance of the Power Apps Checker service to use.
- `--customEndpoint` (`-ce`) - Specify a custom URL as the Power Apps Checker endpoint.
- `--ruleLevelOverride` (`-rl`) - Path to a file containing a JSON array rules and levels to override. Accepted values for OverrideLevel are: Critical, High, Medium, Low, Informational. Example: [{"Id":"meta-remove-dup-reg","OverrideLevel":"Medium"},{"Id":"il-avoid-specialized-update-ops","OverrideLevel":"Medium"}]
- `--ruleSet` (`-rs`) - Select a rule set that is executed as part of this build. Values: A valid Guid, "AppSource Certification", "Solution Checker" (default).
- `--excludedFiles` (`-ef`) - Exclude Files from the Analysis. Pass as comma-separated values
- `--saveResults` (`-sav`) - Uses current environment to store solution analysis results that can be seen in Solution Health Hub App. By default, this argument is set to false.
- `--clearCache` (`-cc`) - Clears the solution checker enforcement cache, for your tenant, of all records that pertain to past results for your solutions.

