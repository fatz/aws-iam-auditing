# AWS IAM Auditing

this tool collects for every active AWS Organizations Account the credential report and parses it through a Jinja2 template the resulting overview Report will be send by Email.

It expects working credentials for calling `sts:AssumeRole` into all sub accounts as well as `iam:GenerateCredentialReport`, `iam:GetCredentialReport`

```
usage: awsiamreport.py [-h] [--blacklisted BLACKLISTED [BLACKLISTED ...]]
                       [--roleName ROLENAME [ROLENAME ...]]
                       [--smtp-server [SMTP_SERVER]] [--smtp-port [SMTP_PORT]]
                       [--smtp-ssl] [--smtp-user [SMTP_USER]]
                       [--smtp-password [SMTP_PASSWORD]]
                       [--smtp-to SMTP_TO [SMTP_TO ...]]
                       [--smtp-from [SMTP_FROM]]

optional arguments:
  -h, --help            show this help message and exit
  --blacklisted BLACKLISTED [BLACKLISTED ...], -b BLACKLISTED [BLACKLISTED ...]
                        blacklisted accounts are getting ignored
  --roleName ROLENAME [ROLENAME ...], -r ROLENAME [ROLENAME ...]
                        role name to use for assume
  --smtp-server [SMTP_SERVER]
                        the smtp server to use
  --smtp-port [SMTP_PORT]
                        smtp port
  --smtp-ssl            use ssl
  --smtp-user [SMTP_USER]
                        smtp user
  --smtp-password [SMTP_PASSWORD]
                        smtp users password
  --smtp-to SMTP_TO [SMTP_TO ...]
                        email address(es) receiving the report
  --smtp-from [SMTP_FROM]
                        email address used as from
```
