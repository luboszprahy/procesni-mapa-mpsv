# admin assign-user

Assign a user to a target Dataverse environment with specified security role.

## Arguments

- `--environment` (`-env`) - ID or URL of the environment to assign a user to.
- `--user` (`-u`) - Object ID or user principal name (UPN) of Microsoft Entra ID user to be assigned to the environment or Application ID if assigning an Application User.
- `--role` (`-r`) - Name or ID of security role to be applied to user
- `--application-user` (`-au`) - Specifies whether the input user is an application user. If a business unit isn't specified, the application user is added to the authenticated users business unit.
- `--business-unit` (`-bu`) - ID of business unit to associate application user with.
- `--async` (`-a`) - Optional boolean argument to run pac verbs asynchronously, defaults to false.

