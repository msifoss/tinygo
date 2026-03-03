---
status: draft
---

title: "TinyGo: Create Dedicated AWS Account Under SSO Org for Internal Tooling"
type: Issue
priority: 2
tags: "TinyGo; AWS; SSO; Account; Infrastructure"
description: |
  <h2>TL;DR</h2>
  <p>We need a new, separate AWS account under the membersolutions SSO organization for
  TinyGo &mdash; an internal tool that securely shares HTML content (reports, dashboards,
  presentations) with authenticated users. This keeps TinyGo resources isolated from
  CallHero and other production workloads.</p>

  <h2>Description</h2>
  <p>TinyGo deploys static HTML sites to S3 behind CloudFront with Cognito-based
  authentication (login page + MFA). It requires its own AWS account to maintain
  blast radius isolation from existing workloads in account 653614598774 (MS-Marketing /
  CallHero). The account will host S3 buckets, a CloudFront distribution, a Cognito User
  Pool, and Lambda@Edge functions.</p>

  <h2>Dependency</h2>
  <p><strong>Blocked by:</strong> "TinyGo: Create ADO Repository in DevOps Project"
  &mdash; repo should be in ADO before proceeding with infrastructure work.<br/>
  <strong>Blocks:</strong> "TinyGo: Create SSO Permission Set with IAM Permissions for New Account"
  &mdash; the permission set ticket requires this account to exist first.</p>

  <h2>What's Needed</h2>
  <p><strong>Create a new AWS account under the membersolutions AWS Organization and add it to SSO.</strong></p>

  <h2>Steps to Complete</h2>
  <table border="1" cellpadding="6" cellspacing="0">
  <tr style="background-color:#1B3A5C;color:#FFFFFF;"><th>Step</th><th>Action</th></tr>
  <tr><td>1</td><td>Create a new AWS account under the membersolutions Organization<br/>
  <strong>Suggested name:</strong> <code>MSI-InternalTools</code> or <code>MSI-TinyGo</code><br/>
  <strong>Email:</strong> aws-internaltools@membersolutions.com (or appropriate alias)</td></tr>
  <tr style="background-color:#F2F6FA;"><td>2</td><td>Add the new account to AWS SSO (IAM Identity Center) under the membersolutions org<br/>
  SSO start URL: <code>https://membersolutions.awsapps.com/start</code></td></tr>
  <tr><td>3</td><td>Assign user <code>cfossenier</code> to the new account with a permission set (see related ticket for permission set details)</td></tr>
  <tr style="background-color:#F2F6FA;"><td>4</td><td><strong>Verify:</strong> Confirm cfossenier can authenticate to the new account via SSO:<br/>
  <code>aws sso login</code><br/>
  <code>aws sts get-caller-identity</code><br/>
  Expected: new account ID in the response</td></tr>
  </table>

  <h2>Background</h2>
  <p>TinyGo was initially deployed to account 653614598774 (MS-Marketing) but this shares
  infrastructure with CallHero and other production workloads. A dedicated account provides:</p>
  <ul>
  <li>Resource isolation &mdash; TinyGo resources cannot interfere with CallHero</li>
  <li>Cleaner billing &mdash; TinyGo costs tracked separately</li>
  <li>Simpler permissions &mdash; broader access within a scoped account vs. narrow permissions in a shared one</li>
  <li>Independent lifecycle &mdash; can be torn down without affecting other projects</li>
  </ul>

  <h2>Reference</h2>
  <table border="1" cellpadding="6" cellspacing="0">
  <tr style="background-color:#1B3A5C;color:#FFFFFF;"><th>Item</th><th>Value</th></tr>
  <tr><td>SSO Org</td><td><code>https://membersolutions.awsapps.com/start</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>Existing Account</td><td>653614598774 (MS-Marketing) &mdash; do NOT use for TinyGo</td></tr>
  <tr><td>User</td><td><code>cfossenier</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>Repo</td><td><a href="https://github.com/msifoss/tinygo">msifoss/tinygo</a></td></tr>
  </table>

  <h2>Impact if Not Resolved</h2>
  <p>TinyGo cannot be deployed. The team currently has no secure mechanism to share
  HTML reports and presentations with authenticated access. The alternative is using
  unsecured file sharing or the tiiny.host third-party service.</p>

  <h2>Estimated Time</h2>
  <p><strong>15&ndash;30 minutes</strong> (account creation + SSO assignment + verification)</p>

  <h2>Contact</h2>
  <p><strong>Requestor:</strong> Chris Fossenier<br/>
  <strong>Email:</strong> cfossenier@membersolutions.com<br/>
  Available for questions or a quick call if needed.</p>
