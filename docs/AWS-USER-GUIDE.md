# TinyGo AWS User Guide

Share static HTML sites securely via AWS with Cognito-based authentication. Only users you explicitly create can access your sites.

---

## Overview

TinyGo AWS deploys HTML files to **S3** behind **CloudFront** (CDN), protected by **Cognito** (user authentication). When someone visits your site URL in a browser, they're prompted to log in. Only users you've created in your Cognito User Pool can see the content.

### How authentication works

```
Browser visits site
  -> Lambda@Edge checks for auth cookie
  -> No cookie? Redirect to Cognito login page
  -> User enters email + password
  -> Cognito redirects back with secure cookies set
  -> Site loads
  -> Cookies valid for 1 hour, then re-login required
```

All cookies are `Secure` (HTTPS only), `HttpOnly` (no JavaScript access), and `SameSite=Lax` (CSRF protection).

CLI deploys use Bearer token authentication and are unaffected by the browser login flow.

---

## Quick Start

### Prerequisites

- Python 3.9+
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with credentials (`aws configure`)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

### 1. Install TinyGo

```bash
git clone https://github.com/msifoss/tinygo.git
cd tinygo
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Provision infrastructure

```bash
tinygo aws init --domain-prefix my-company-sites
```

This creates all AWS resources (S3 bucket, CloudFront distribution, Cognito User Pool, Lambda@Edge auth) in a single command. The `--domain-prefix` must be globally unique across all AWS accounts.

The command runs a **two-phase deploy** — first to create the infrastructure, then to configure the Lambda function with the correct CloudFront domain and Cognito client secret.

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--region` | `us-east-1` | AWS region |
| `--stack-name` | `tinygo-hosting` | CloudFormation stack name |
| `--domain-prefix` | *(required)* | Cognito Hosted UI domain prefix |
| `--guided` | off | Interactive SAM deploy prompts |

### 3. Deploy a site

```bash
tinygo aws deploy index.html --site quarterly-report
```

### 4. Share the URL

The deploy command prints the CloudFront URL:

```
Deployed! 1 files uploaded.
URL: https://d1abc2def3.cloudfront.net/sites/quarterly-report/index.html
```

Share this URL with your team. They'll see a login page until you create accounts for them.

---

## Managing Users

All user management is done through the **AWS Console** or **AWS CLI**.

### Creating users (AWS Console)

1. Open the [AWS Cognito Console](https://console.aws.amazon.com/cognito/v2/idp/user-pools)
2. Select your user pool (default name: **tinygo-users**)
3. Go to the **Users** tab
4. Click **Create user**
5. Fill in:
   - **User name**: their email address
   - **Email address**: same email
   - **Mark email as verified**: check this box
   - **Temporary password**: set one, or choose "Generate a password"
6. Click **Create user**
7. Send them the site URL and their temporary password
8. On first login, they'll be prompted to set their own password

### Creating users (AWS CLI)

```bash
# Create a user with a temporary password
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username user@company.com \
  --user-attributes Name=email,Value=user@company.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!@#"

# The user must change their password on first login
```

Replace `us-east-1_XXXXXXXXX` with your User Pool ID (shown in `tinygo aws status` output as `cognito_user_pool_id`).

### Disabling a user

```bash
aws cognito-idp admin-disable-user \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username user@company.com
```

Disabled users cannot log in. Their existing sessions expire naturally (within 1 hour).

### Re-enabling a user

```bash
aws cognito-idp admin-enable-user \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username user@company.com
```

### Deleting a user

```bash
aws cognito-idp admin-delete-user \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username user@company.com
```

### Resetting a user's password

If a user forgets their password, you can force a reset:

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username user@company.com \
  --password "NewTempPass456!@#" \
  --no-permanent
```

The `--no-permanent` flag forces them to choose a new password at next login. Use `--permanent` to set a permanent password directly.

---

## Multi-Factor Authentication (MFA)

MFA is **already enabled** on your Cognito User Pool in optional mode. Users can set it up themselves — no infrastructure changes needed.

### How users enable MFA

1. Log in to the Cognito Hosted UI
2. On first login (or when prompted), choose to set up MFA
3. Scan the QR code with an authenticator app (Google Authenticator, Authy, 1Password, etc.)
4. Enter the 6-digit code to confirm
5. Future logins require the code from their authenticator app

### Enforcing MFA for all users

If you want to **require** MFA (not just make it optional), change the `MfaConfiguration` in `infra/template.yaml`:

```yaml
# Before (current setting)
MfaConfiguration: OPTIONAL

# After (enforced for all users)
MfaConfiguration: "ON"
```

Then redeploy the stack:

```bash
tinygo aws init --domain-prefix your-existing-prefix
```

### Resetting a user's MFA

If a user loses access to their authenticator app, you can reset their MFA so they can set it up again:

```bash
# Remove the user's MFA TOTP device
aws cognito-idp admin-set-user-mfa-preference \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username user@company.com \
  --software-token-mfa-settings Enabled=false,PreferredMfa=false

# Also reset their password so they go through the full setup flow again
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username user@company.com \
  --password "TempReset789!@#" \
  --no-permanent
```

On next login, they'll set a new password and be prompted to configure MFA again.

---

## Site Management

### Deploy a new site

```bash
tinygo aws deploy index.html --site my-report
```

HTML files with local references (CSS, JS, images) are automatically bundled. Use `--no-bundle` to deploy a single file as-is.

### Update an existing site

```bash
tinygo aws update index.html --site my-report
```

### Delete a site

```bash
tinygo aws delete --site my-report
# Delete site 'my-report' from S3? [y/N]: y

# Skip confirmation
tinygo aws delete --site my-report --yes
```

### List all sites

```bash
tinygo aws list
```

### Check configuration

```bash
tinygo aws status
```

---

## Security Summary

| Layer | Protection |
|-------|-----------|
| **S3 bucket** | No public access; CloudFront OAC only |
| **CloudFront** | HTTPS enforced (HTTP redirected) |
| **Authentication** | Cognito User Pool with email verification |
| **Cookies** | `Secure; HttpOnly; SameSite=Lax` |
| **Passwords** | 12+ chars, uppercase, lowercase, numbers, symbols required |
| **MFA** | Optional TOTP (authenticator app), can be enforced |
| **Session duration** | 1 hour (cookie `Max-Age`), then re-login required |
| **Lambda@Edge** | JWT signature verified (RS256) against Cognito JWKS |

---

## Troubleshooting

### "sam CLI not found" or "aws CLI not found"

Install the required tools:
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

### User says "I see a login page but can't log in"

They don't have an account. Create one for them — see [Creating users](#creating-users-aws-console) above.

### User says "My password was rejected"

Passwords must be at least 12 characters with uppercase, lowercase, numbers, and symbols. Example of a valid password: `MySecure#Pass42`

### User is locked out after too many failed attempts

Cognito temporarily locks accounts after repeated failures. Wait 15 minutes, or reset their password:

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id us-east-1_XXXXXXXXX \
  --username user@company.com \
  --password "NewTempPass!23" \
  --no-permanent
```

### "Auth configuration missing" when visiting the site

The Lambda@Edge function doesn't have its config.json. Re-run `tinygo aws init --domain-prefix your-prefix` to redeploy with the correct configuration.

### Finding your User Pool ID

```bash
tinygo aws status
# Look for cognito_user_pool_id in the output
```

Or check `~/.tinygo/config.yaml` under the `aws:` section.
