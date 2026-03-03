---
status: draft
---

title: "TinyGo: Create ADO Repository in DevOps Project"
type: Issue
priority: 2
tags: "TinyGo; ADO; Repository; DevOps"
description: |
  <h2>TL;DR</h2>
  <p>We need a new Git repository called <code>tinygo</code> created in the
  membersolutionsinc/DevOps ADO project so we can migrate the codebase from GitHub
  and manage it alongside our other internal tooling.</p>

  <h2>Description</h2>
  <p>TinyGo is an internal CLI tool for securely deploying and sharing static HTML sites
  (reports, dashboards, presentations) with authenticated users. The code currently lives
  in a GitHub repository (<a href="https://github.com/msifoss/tinygo">msifoss/tinygo</a>)
  and needs to move to Azure DevOps for consistency with our other projects (e.g. CallHero /
  callsync-hubspot). Once the repo is created, we will handle the migration of code and
  history ourselves.</p>

  <h2>Dependency</h2>
  <p><strong>Blocks:</strong> All other TinyGo tickets (AWS account creation, permission set,
  failed stack cleanup) &mdash; we need the repo in ADO before proceeding with
  infrastructure work.</p>

  <h2>What's Needed</h2>
  <p><strong>Create an empty Git repository named <code>tinygo</code> in the membersolutionsinc/DevOps ADO project and grant cfossenier contributor access.</strong></p>

  <h2>Steps to Complete</h2>
  <table border="1" cellpadding="6" cellspacing="0">
  <tr style="background-color:#1B3A5C;color:#FFFFFF;"><th>Step</th><th>Action</th></tr>
  <tr><td>1</td><td>Navigate to <a href="https://dev.azure.com/membersolutionsinc/DevOps/_git">DevOps project repos</a></td></tr>
  <tr style="background-color:#F2F6FA;"><td>2</td><td>Create a new Git repository:<br/>
  <strong>Name:</strong> <code>tinygo</code><br/>
  <strong>Initialize:</strong> Empty (no README or .gitignore &mdash; we will push existing code)</td></tr>
  <tr><td>3</td><td>Grant <code>cfossenier</code> Contributor permissions on the repo</td></tr>
  <tr style="background-color:#F2F6FA;"><td>4</td><td><strong>Verify:</strong> Confirm cfossenier can clone the repo:<br/>
  <code>git clone https://membersolutionsinc@dev.azure.com/membersolutionsinc/DevOps/_git/tinygo</code><br/>
  Expected: successful clone of empty repository</td></tr>
  </table>

  <h2>Background</h2>
  <p>TinyGo is a Python CLI tool that wraps the tiiny.host API and AWS services (S3,
  CloudFront, Cognito) to provide authenticated static site hosting. The project includes
  infrastructure-as-code (SAM/CloudFormation templates), a Lambda@Edge auth function,
  and a comprehensive test suite. Moving to ADO aligns it with our standard toolchain
  and will enable future CI/CD pipeline integration.</p>

  <h2>Reference</h2>
  <table border="1" cellpadding="6" cellspacing="0">
  <tr style="background-color:#1B3A5C;color:#FFFFFF;"><th>Item</th><th>Value</th></tr>
  <tr><td>ADO Organization</td><td><code>membersolutionsinc</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>ADO Project</td><td><code>DevOps</code></td></tr>
  <tr><td>Repo Name</td><td><code>tinygo</code></td></tr>
  <tr style="background-color:#F2F6FA;"><td>Current Location</td><td><a href="https://github.com/msifoss/tinygo">github.com/msifoss/tinygo</a></td></tr>
  <tr><td>Assigned To</td><td>Muhammad</td></tr>
  </table>

  <h2>Impact if Not Resolved</h2>
  <p>TinyGo code remains in a personal GitHub repo, outside the team's standard DevOps
  workflow. This blocks CI/CD pipeline setup and is inconsistent with how other internal
  projects are managed.</p>

  <h2>Estimated Time</h2>
  <p><strong>5 minutes</strong> (create repo + set permissions)</p>

  <h2>Contact</h2>
  <p><strong>Requestor:</strong> Chris Fossenier<br/>
  <strong>Email:</strong> cfossenier@membersolutions.com<br/>
  Available for questions or a quick call if needed.</p>
