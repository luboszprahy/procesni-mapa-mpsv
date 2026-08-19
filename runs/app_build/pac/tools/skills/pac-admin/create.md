# admin create

Creates a Dataverse instance in your tenant.

## Arguments

- `--name` (`-n`) - Sets the name of the environment.
- `--region` (`-r`) - Sets the environment's region name. [defaults to unitedstates]
- `--type` (`-t`) - Sets the environment Type.
- `--currency` (`-c`) - Sets the currency used for your environment. [defaults to USD]
- `--language` (`-l`) - Sets the language used for your environment. [defaults to English]
- `--templates` (`-tm`) - Sets the Dynamics 365 app that needs to be deployed, passed as comma separated values. For example: -tm "D365_Sample, D365_Sales"
- `--domain` (`-d`) - The domain name is part of the environment URL. If domain name is already in use, a numeric value is appended to the domain name. For example: If 'contoso' is already in use, then the environment URL is updated to https://{contoso}0.crm.dynamics.com.
- `--input-file` (`-if`) - The verb arguments to be passed in a .json input file. For example: {"name" : "contoso"}. The arguments passed through command-line will take precedence over arguments from the .json input file.
- `--async` (`-a`) - Optional boolean argument to run pac verbs asynchronously, defaults to false.
- `--security-group-id` (`-sgid`) - Microsoft Entra ID Security Group Id or Microsoft 365 Group Id (required for Teams environment).
- `--max-async-wait-time` (`-wt`) - Max asynchronous wait time in minutes. The default value is 60 minutes.
- `--user` (`-u`) - Object ID or user principal name (UPN) of Microsoft Entra ID user to be assigned to the environment.

