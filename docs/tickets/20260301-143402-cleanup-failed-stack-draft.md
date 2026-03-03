---
status: draft
---

title: "TinyGo: Clean Up Failed CloudFormation Stack (MS-Marketing 653614598774)"
type: Issue
priority: 2
tags: "TinyGo; AWS; IAM; CloudFormation; Cleanup"
description: |
  <h2>TL;DR</h2>
  <p>A CloudFormation stack deployment failed because the PowerUserAccess role lacks IAM
  permissions. The stack is stuck in <code>DELETE_FAILED</code> state and needs an admin
  to remove the orphaned IAM role and delete the stack.</p>

  <h2>Description</h2>
  <p>During initial provisioning of TinyGo hosting infrastructure, the SAM/CloudFormation
  stack <code>tinygo-hosting</code> failed to create because <code>AWSPowerUserAccess</code>
  does not include <code>iam:CreateRole</code>. The stack rolled back but cannot fully
  delete because the rollback also requires IAM permissions
  (<code>iam:DetachRolePolicy</code>). The stack is now stuck in
  <code>DELETE_FAILED</code> state with one orphaned IAM role.</p>

  <h2>Dependency</h2>
  <p><strong>Blocked by:</strong> "TinyGo: Create ADO Repository in DevOps Project"
  &mdash; repo should be in ADO before proceeding with infrastructure work.</p>

  <h2>What's Needed</h2>
  <p><strong>Delete the orphaned IAM role and the failed CloudFormation stack from account 653614598774.</strong></p>

  <h2>Steps to Complete</h2>
  <table border="1" cellpadding="6" cellspacing="0">
  <tr style="background-color:#1B3A5C;color:#FFFFFF;"><th>Step</th><th>Action</th></tr>
  <tr><td>1</td><td>Delete the orphaned IAM role:<br/>
  <code>aws iam detach-role-policy --role-name tinygo-hosting-AuthFunctionRole-aNqiSyjYm4ph --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --region us-east-1</code><br/>
  <code>aws iam delete-role --role-name tinygo-hosting-AuthFunctionRole-aNqiSyjYm4ph --region us-east-1</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>2</td><td>Delete the stuck CloudFormation stack:<br/>
  <code>aws cloudformation delete-stack --stack-name tinygo-hosting --region us-east-1</code></td></tr>
  <tr><td>3</td><td><strong>Verify:</strong> Confirm the stack is fully deleted:<br/>
  <code>aws cloudformation describe-stacks --stack-name tinygo-hosting --region us-east-1</code><br/>
  Expected: <code>Stack with id tinygo-hosting does not exist</code></td></tr>
  </table>

  <h2>Background</h2>
  <p>TinyGo is an internal tool for securely sharing static HTML sites (reports, dashboards,
  presentations) with authenticated users via S3 + CloudFront + Cognito. This stack was a
  first deployment attempt that failed due to insufficient IAM permissions on the
  PowerUserAccess SSO role. The TinyGo infrastructure will be re-deployed to a separate,
  dedicated AWS account (see related ticket).</p>

  <h2>Reference</h2>
  <table border="1" cellpadding="6" cellspacing="0">
  <tr style="background-color:#1B3A5C;color:#FFFFFF;"><th>Item</th><th>Value</th></tr>
  <tr><td>Account</td><td>653614598774 (MS-Marketing)</td></tr>
  <tr style="background-color:#F2F6FA;"><td>Region</td><td>us-east-1</td></tr>
  <tr><td>Stack Name</td><td><code>tinygo-hosting</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>Orphaned Role</td><td><code>tinygo-hosting-AuthFunctionRole-aNqiSyjYm4ph</code></td></tr>
  <tr><td>Repo</td><td><a href="https://github.com/msifoss/tinygo">msifoss/tinygo</a></td></tr>
  </table>

  <h2>Impact if Not Resolved</h2>
  <p>No operational impact &mdash; the stack never completed deployment. The orphaned role
  and failed stack are just clutter in the account. However, the stack name
  <code>tinygo-hosting</code> cannot be reused until deleted.</p>

  <h2>Estimated Time</h2>
  <p><strong>5 minutes</strong> (two CLI commands + verification)</p>

  <h2>Contact</h2>
  <p><strong>Requestor:</strong> Chris Fossenier<br/>
  <strong>Email:</strong> cfossenier@membersolutions.com<br/>
  Available for questions or a quick call if needed.</p>
