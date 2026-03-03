---
status: draft
---

title: "TinyGo: Create SSO Permission Set with IAM Permissions for New Account"
type: Issue
priority: 2
tags: "TinyGo; AWS; SSO; IAM; Permissions"
description: |
  <h2>TL;DR</h2>
  <p>We need an SSO permission set for the new TinyGo AWS account that includes
  PowerUserAccess plus IAM role management permissions. These IAM permissions are required
  because TinyGo's CloudFormation/SAM stack creates a Lambda@Edge execution role as part
  of its infrastructure deployment.</p>

  <h2>Description</h2>
  <p>TinyGo uses AWS SAM (CloudFormation) to deploy infrastructure including a Lambda@Edge
  function. CloudFormation needs to create, update, and delete the Lambda execution role
  automatically. The standard <code>AWSPowerUserAccess</code> managed policy does not
  include IAM write permissions, so a custom permission set is needed that adds scoped
  IAM role management on top of PowerUserAccess.</p>

  <h2>Dependency</h2>
  <p><strong>Blocked by:</strong> "TinyGo: Create ADO Repository in DevOps Project"
  &mdash; repo should be in ADO before proceeding with infrastructure work.<br/>
  <strong>Blocked by:</strong> "TinyGo: Create Dedicated AWS Account Under SSO Org for Internal Tooling"
  &mdash; the new account must exist before the permission set can be assigned to it.</p>

  <h2>What's Needed</h2>
  <p><strong>Create an SSO permission set with PowerUserAccess + scoped IAM permissions and assign it to cfossenier on the new TinyGo account.</strong></p>

  <h2>Steps to Complete</h2>
  <table border="1" cellpadding="6" cellspacing="0">
  <tr style="background-color:#1B3A5C;color:#FFFFFF;"><th>Step</th><th>Action</th></tr>
  <tr><td>1</td><td>Create a new SSO permission set named <code>TinyGoAdmin</code> (or similar)<br/>
  <strong>Session duration:</strong> 4 hours (or org default)<br/>
  <strong>Managed policy:</strong> Attach <code>PowerUserAccess</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>2</td><td>Add an inline policy for scoped IAM permissions (see JSON below):<br/>
  <pre><code>{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "TinyGoIAMRoleManagement",
        "Effect": "Allow",
        "Action": [
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:GetRole",
          "iam:PassRole",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy"
        ],
        "Resource": "arn:aws:iam::*:role/tinygo-*"
      }
    ]
  }</code></pre>
  <p><strong>Note:</strong> The <code>Resource</code> uses <code>*</code> for the account ID
  because the new account ID is not yet known. This can be tightened to the specific
  account ID after creation. The <code>tinygo-*</code> prefix scoping ensures these
  permissions only apply to roles created by the TinyGo CloudFormation stack.</p></td></tr>
  <tr><td>3</td><td>Assign the <code>TinyGoAdmin</code> permission set to user <code>cfossenier</code> on the new TinyGo account</td></tr>
  <tr style="background-color:#F2F6FA;"><td>4</td><td><strong>Verify:</strong> Confirm cfossenier can create IAM roles in the new account:<br/>
  <code>aws sso login --profile tinygo</code><br/>
  <code>aws iam create-role --role-name tinygo-test-role --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' --profile tinygo</code><br/>
  <code>aws iam delete-role --role-name tinygo-test-role --profile tinygo</code><br/>
  Expected: role created and deleted successfully</td></tr>
  </table>

  <h2>Background</h2>
  <p>TinyGo's SAM template (<code>infra/template.yaml</code>) defines an
  <code>AuthFunctionRole</code> IAM role that CloudFormation creates automatically during
  <code>sam deploy</code>. This role allows the Lambda@Edge function to assume execution
  permissions. Without <code>iam:CreateRole</code>, the stack deployment fails &mdash; as
  we discovered when attempting to deploy to account 653614598774 with PowerUserAccess.</p>
  <p>The inline policy is scoped to <code>arn:aws:iam::*:role/tinygo-*</code> so the
  permissions only apply to roles whose names start with <code>tinygo-</code>. CloudFormation
  auto-generates role names prefixed with the stack name (<code>tinygo-hosting-</code>),
  so this scope covers all stack-managed roles without granting broad IAM access.</p>

  <h2>Reference</h2>
  <table border="1" cellpadding="6" cellspacing="0">
  <tr style="background-color:#1B3A5C;color:#FFFFFF;"><th>Item</th><th>Value</th></tr>
  <tr><td>SSO Org</td><td><code>https://membersolutions.awsapps.com/start</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>Target Account</td><td>New TinyGo account (created in related ticket)</td></tr>
  <tr><td>User</td><td><code>cfossenier</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>Permission Set Name</td><td><code>TinyGoAdmin</code> (suggested)</td></tr>
  <tr><td>IAM Scope</td><td><code>arn:aws:iam::*:role/tinygo-*</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>Repo</td><td><a href="https://github.com/msifoss/tinygo">msifoss/tinygo</a></td></tr>
  </table>

  <h2>Impact if Not Resolved</h2>
  <p>TinyGo's infrastructure stack cannot be deployed. The <code>sam deploy</code> command
  will fail with <code>iam:CreateRole</code> access denied, exactly as it did on the
  previous attempt in account 653614598774.</p>

  <h2>Estimated Time</h2>
  <p><strong>15 minutes</strong> (create permission set + attach inline policy + assign to user + verify)</p>

  <h2>Contact</h2>
  <p><strong>Requestor:</strong> Chris Fossenier<br/>
  <strong>Email:</strong> cfossenier@membersolutions.com<br/>
  Available for questions or a quick call if needed.</p>
