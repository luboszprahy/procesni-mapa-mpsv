# auth create

Create and store authentication profiles on this computer

## Arguments

- `--name` (`-n`) - The name you want to give to this authentication profile (maximum 30 characters).
- `--url` (`-u`) - The resource URL to connect to
- `--username` (`-un`) - Optional: The username to authenticate with; shows a Microsoft Entra ID dialog if not specified.
- `--password` (`-p`) - Optional: The password to authenticate with
- `--applicationId` (`-id`) - Optional: The application ID to authenticate with.
- `--clientSecret` (`-cs`) - Optional: The client secret to authenticate with
- `--certificateDiskPath` (`-cdp`) - Optional: The certificate disk path to authenticate with
- `--certificatePassword` (`-cp`) - Optional: The certificate password to authenticate with
- `--tenant` (`-t`) - Tenant ID if using application ID/client secret or application ID/client certificate.
- `--cloud` (`-ci`) - Optional: The cloud instance to authenticate with
- `--deviceCode` (`-dc`) - Use the Microsoft Entra ID Device Code flow for interactive sign-in.
- `--managedIdentity` (`-mi`) - Use default Azure identity.
- `--githubFederated` (`-ghf`) - Use GitHub Federation for Service Principal Auth; requires --tenant and --applicationId arguments
- `--azureDevOpsFederated` (`-adof`) - Use Azure DevOps Federation for Service Principal Auth; requires --tenant and --applicationId arguments
- `--environment` (`-env`) - Default environment (ID, url, unique name, or partial name).

