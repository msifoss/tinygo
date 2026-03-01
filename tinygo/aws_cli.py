"""TinyGo AWS CLI — deploy web pages to S3 + CloudFront."""

import json
import shutil
import subprocess
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from tinygo.config import get_aws_config, is_aws_configured, set_aws_config
from tinygo.log import log_event

console = Console()


def _get_aws_client():
    """Return an AWSClient from saved config, or exit with error."""
    try:
        from tinygo.aws_client import AWSClient
    except ImportError:
        console.print(
            "[red]AWS dependencies not installed.[/red] "
            "Run [bold]pip install tinygo\\[aws][/bold] to enable AWS features."
        )
        raise SystemExit(1)

    if not is_aws_configured():
        console.print(
            "[red]AWS not configured.[/red] "
            "Run [bold]tinygo aws init[/bold] first."
        )
        raise SystemExit(1)

    cfg = get_aws_config()
    return AWSClient(
        region=cfg["region"],
        bucket_name=cfg["bucket_name"],
        distribution_id=cfg["distribution_id"],
    )


def _format_size(size_bytes: int) -> str:
    """Return a human-readable size string."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


@click.group()
def aws():
    """Deploy and manage sites on AWS (S3 + CloudFront)."""


# ── init ─────────────────────────────────────────────────────────────────


def _write_lambda_config(infra_dir, config_data):
    """Write config.json into the Lambda@Edge package directory."""
    config_path = infra_dir / "lambda_edge" / "config.json"
    config_path.write_text(json.dumps(config_data, indent=2))


def _get_client_secret(region, pool_id, client_id):
    """Retrieve the Cognito app client secret via AWS CLI."""
    result = subprocess.run(
        ["aws", "cognito-idp", "describe-user-pool-client",
         "--user-pool-id", pool_id, "--client-id", client_id,
         "--region", region, "--output", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    return data.get("UserPoolClient", {}).get("ClientSecret")


def _sam_build(infra_dir):
    """Run sam build and return True on success."""
    result = subprocess.run(
        ["sam", "build"],
        cwd=str(infra_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]sam build failed:[/red]\n{result.stderr}")
        raise SystemExit(1)


def _sam_deploy(infra_dir, stack_name, region, domain_prefix, guided):
    """Run sam deploy and return True on success."""
    deploy_cmd = [
        "sam", "deploy",
        "--stack-name", stack_name,
        "--region", region,
        "--capabilities", "CAPABILITY_IAM",
        "--no-fail-on-empty-changeset",
        "--parameter-overrides", f"CognitoDomainPrefix={domain_prefix}",
    ]
    if guided:
        deploy_cmd.append("--guided")

    result = subprocess.run(
        deploy_cmd,
        cwd=str(infra_dir),
        capture_output=not guided,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr if not guided else ""
        console.print(f"[red]sam deploy failed:[/red]\n{stderr}")
        raise SystemExit(1)


def _read_stack_outputs(stack_name, region):
    """Read CloudFormation stack outputs, return dict of key→value."""
    result = subprocess.run(
        ["aws", "cloudformation", "describe-stacks",
         "--stack-name", stack_name, "--region", region,
         "--query", "Stacks[0].Outputs", "--output", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]Failed to read stack outputs:[/red]\n{result.stderr}")
        raise SystemExit(1)
    outputs = json.loads(result.stdout)
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


@aws.command()
@click.option("--region", default="us-east-1", help="AWS region.")
@click.option("--stack-name", default="tinygo-hosting", help="CloudFormation stack name.")
@click.option("--domain-prefix", required=True, help="Globally unique Cognito Hosted UI domain prefix.")
@click.option("--guided", is_flag=True, help="Run sam deploy --guided.")
def init(region, stack_name, domain_prefix, guided):
    """Provision AWS infrastructure via SAM and save config.

    Uses a two-phase deploy: Phase 1 creates the stack with a placeholder
    Lambda config, Phase 2 re-deploys with the real config (CloudFront domain,
    client secret) once the stack outputs are known.
    """
    for tool in ("sam", "aws"):
        if not shutil.which(tool):
            console.print(f"[red]{tool} CLI not found.[/red] Install it first.")
            raise SystemExit(1)

    infra_dir = Path(__file__).parent.parent / "infra"
    if not (infra_dir / "template.yaml").exists():
        console.print(f"[red]SAM template not found at {infra_dir}/template.yaml[/red]")
        raise SystemExit(1)

    # ── Phase 1: Deploy with placeholder config ───────────────────────
    console.print("[bold]Phase 1:[/bold] Deploying infrastructure...")
    placeholder_config = {
        "region": region,
        "user_pool_id": "placeholder",
        "client_id": "placeholder",
        "client_secret": "placeholder",
        "cognito_domain": "https://placeholder.auth.us-east-1.amazoncognito.com",
        "callback_url": "https://placeholder.cloudfront.net/_auth/callback",
        "cloudfront_domain": "placeholder.cloudfront.net",
    }
    _write_lambda_config(infra_dir, placeholder_config)

    with console.status("Running sam build (phase 1)..."):
        _sam_build(infra_dir)
    console.print("[green]sam build succeeded (phase 1).[/green]")

    console.print("Running sam deploy (phase 1)...")
    _sam_deploy(infra_dir, stack_name, region, domain_prefix, guided)
    console.print("[green]sam deploy succeeded (phase 1).[/green]")

    # ── Read stack outputs ────────────────────────────────────────────
    with console.status("Reading stack outputs..."):
        output_map = _read_stack_outputs(stack_name, region)

    user_pool_id = output_map.get("UserPoolId", "")
    client_id = output_map.get("UserPoolClientId", "")
    cloudfront_domain = output_map.get("CloudFrontDomain", "")
    cognito_domain_prefix = output_map.get("CognitoDomainPrefix", domain_prefix)

    # Retrieve client secret
    with console.status("Retrieving client secret..."):
        client_secret = _get_client_secret(region, user_pool_id, client_id)
    if not client_secret:
        console.print("[red]Failed to retrieve Cognito client secret.[/red]")
        raise SystemExit(1)

    # ── Phase 2: Re-deploy with real config ───────────────────────────
    console.print("[bold]Phase 2:[/bold] Re-deploying with real configuration...")
    real_config = {
        "region": region,
        "user_pool_id": user_pool_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "cognito_domain": f"https://{cognito_domain_prefix}.auth.{region}.amazoncognito.com",
        "callback_url": f"https://{cloudfront_domain}/_auth/callback",
        "cloudfront_domain": cloudfront_domain,
    }
    _write_lambda_config(infra_dir, real_config)

    with console.status("Running sam build (phase 2)..."):
        _sam_build(infra_dir)
    console.print("[green]sam build succeeded (phase 2).[/green]")

    console.print("Running sam deploy (phase 2)...")
    _sam_deploy(infra_dir, stack_name, region, domain_prefix, guided)
    console.print("[green]sam deploy succeeded (phase 2).[/green]")

    # ── Save config ───────────────────────────────────────────────────
    aws_config = {
        "region": region,
        "bucket_name": output_map.get("BucketName", ""),
        "distribution_id": output_map.get("DistributionId", ""),
        "cloudfront_domain": cloudfront_domain,
        "cognito_user_pool_id": user_pool_id,
        "cognito_client_id": client_id,
        "cognito_domain_prefix": cognito_domain_prefix,
    }
    set_aws_config(aws_config)
    console.print("[green]AWS config saved to ~/.tinygo/config.yaml[/green]")

    table = Table(title="Stack Outputs")
    table.add_column("Key", style="bold")
    table.add_column("Value", style="cyan")
    for k, v in aws_config.items():
        table.add_row(k, v)
    console.print(table)


# ── deploy ───────────────────────────────────────────────────────────────


@aws.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--site", "-s", required=True, help="Site name (S3 prefix).")
@click.option("--no-bundle", is_flag=True, help="Skip bundling linked local files.")
@click.option("--no-invalidate", is_flag=True, help="Skip CloudFront cache invalidation.")
def deploy(file, site, no_bundle, no_invalidate):
    """Deploy a file or HTML project to AWS."""
    from pathlib import Path
    from tinygo.bundle import cleanup_bundle_dir, create_bundle_dir

    client = _get_aws_client()

    if client.site_exists(site):
        console.print(
            f"[red]Site '{site}' already exists.[/red] "
            "Use [bold]tinygo aws update[/bold] instead."
        )
        raise SystemExit(1)

    staging_dir = None
    try:
        if no_bundle:
            # Use the file's parent directory as-is (single file)
            file_path = Path(file).resolve()
            staging_dir = file_path.parent
            is_temp = False
        else:
            with console.status("Bundling..."):
                staging_dir = create_bundle_dir(file)
            is_temp = True

        with console.status("Uploading to S3..."):
            keys = client.upload_site(site, staging_dir)

        if not no_invalidate:
            with console.status("Invalidating CloudFront cache..."):
                inv_id = client.invalidate_cache(site)
            console.print(f"[dim]Invalidation: {inv_id}[/dim]")

        cfg = get_aws_config()
        domain = cfg.get("cloudfront_domain", "")
        url = f"https://{domain}/sites/{site}/index.html"

        log_event("AWS_DEPLOY", site, success=True, file_path=file, url=url)
        console.print(f"[green]Deployed![/green] {len(keys)} files uploaded.")
        console.print(f"[bold]URL:[/bold] {url}")

    except Exception as e:
        if not isinstance(e, SystemExit):
            from tinygo.aws_client import AWSError
            detail = e.detail if isinstance(e, AWSError) else str(e)
            log_event("AWS_DEPLOY", site, success=False, file_path=file, error=detail)
            console.print(f"[red]Deploy failed:[/red] {detail}")
            raise SystemExit(1)
        raise
    finally:
        if staging_dir and is_temp:
            cleanup_bundle_dir(staging_dir)


# ── update ───────────────────────────────────────────────────────────────


@aws.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--site", "-s", required=True, help="Site name (S3 prefix).")
@click.option("--no-bundle", is_flag=True, help="Skip bundling linked local files.")
@click.option("--no-invalidate", is_flag=True, help="Skip CloudFront cache invalidation.")
def update(file, site, no_bundle, no_invalidate):
    """Update an existing AWS-hosted site with new content."""
    from pathlib import Path
    from tinygo.bundle import cleanup_bundle_dir, create_bundle_dir

    client = _get_aws_client()

    if not client.site_exists(site):
        console.print(
            f"[red]Site '{site}' does not exist.[/red] "
            "Use [bold]tinygo aws deploy[/bold] first."
        )
        raise SystemExit(1)

    staging_dir = None
    is_temp = False
    try:
        if no_bundle:
            file_path = Path(file).resolve()
            staging_dir = file_path.parent
        else:
            with console.status("Bundling..."):
                staging_dir = create_bundle_dir(file)
            is_temp = True

        with console.status("Uploading to S3..."):
            keys = client.upload_site(site, staging_dir)

        if not no_invalidate:
            with console.status("Invalidating CloudFront cache..."):
                inv_id = client.invalidate_cache(site)
            console.print(f"[dim]Invalidation: {inv_id}[/dim]")

        cfg = get_aws_config()
        domain = cfg.get("cloudfront_domain", "")
        url = f"https://{domain}/sites/{site}/index.html"

        log_event("AWS_UPDATE", site, success=True, file_path=file, url=url)
        console.print(f"[green]Updated![/green] {len(keys)} files uploaded.")
        console.print(f"[bold]URL:[/bold] {url}")

    except Exception as e:
        if not isinstance(e, SystemExit):
            from tinygo.aws_client import AWSError
            detail = e.detail if isinstance(e, AWSError) else str(e)
            log_event("AWS_UPDATE", site, success=False, file_path=file, error=detail)
            console.print(f"[red]Update failed:[/red] {detail}")
            raise SystemExit(1)
        raise
    finally:
        if staging_dir and is_temp:
            cleanup_bundle_dir(staging_dir)


# ── delete ───────────────────────────────────────────────────────────────


@aws.command()
@click.option("--site", "-s", required=True, help="Site name to delete.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def delete(site, yes):
    """Delete an AWS-hosted site."""
    client = _get_aws_client()

    if not yes:
        click.confirm(f"Delete site '{site}' from S3?", abort=True)

    with console.status("Deleting from S3..."):
        count = client.delete_site(site)

    if count == 0:
        console.print(f"[yellow]No files found for site '{site}'.[/yellow]")
    else:
        log_event("AWS_DELETE", site, success=True)
        console.print(f"[green]Deleted[/green] {count} files from '{site}'.")


# ── list ─────────────────────────────────────────────────────────────────


@aws.command(name="list")
def list_sites():
    """List all AWS-hosted sites."""
    client = _get_aws_client()

    with console.status("Listing sites..."):
        sites = client.list_sites()

    if not sites:
        console.print("No sites found.")
        return

    table = Table(title="AWS Sites")
    table.add_column("Name", style="cyan")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")
    for s in sites:
        table.add_row(s["name"], str(s["file_count"]), _format_size(s["total_size"]))
    console.print(table)


# ── status ───────────────────────────────────────────────────────────────


@aws.command()
def status():
    """Show AWS configuration status."""
    if not is_aws_configured():
        console.print("[yellow]AWS not configured.[/yellow] Run [bold]tinygo aws init[/bold].")
        return

    cfg = get_aws_config()
    table = Table(title="AWS Configuration")
    table.add_column("Key", style="bold")
    table.add_column("Value", style="cyan")
    for k, v in cfg.items():
        table.add_row(k, str(v))
    console.print(table)
