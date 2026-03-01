"""TinyGo CLI — deploy web pages to tiiny.host."""

import click
from rich.console import Console
from rich.table import Table

from tinygo.api import TiinyClient, TiinyError
from tinygo.bundle import cleanup_bundle, create_bundle
from tinygo.config import get_api_key, get_config, mask_key, set_api_key
from tinygo.log import clear_log, log_event, read_log

console = Console()


def _get_client(api_key: str | None) -> TiinyClient:
    """Resolve the API key and return a TiinyClient, or exit with an error."""
    key = get_api_key(api_key)
    if not key:
        console.print(
            "[red]No API key configured.[/red] "
            "Run [bold]tinygo config set-key[/bold] or pass --api-key."
        )
        raise SystemExit(1)
    return TiinyClient(key)


@click.group()
@click.version_option(package_name="tinygo")
def main():
    """TinyGo — deploy web pages to tiiny.host."""


# ── deploy ───────────────────────────────────────────────────────────────


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--domain", "-d", default=None, help="Subdomain for the site.")
@click.option("--password", "-p", default=None, help="Password-protect the site.")
@click.option("--bundle", "-b", is_flag=True, help="Bundle linked local files into a zip.")
@click.option("--api-key", default=None, envvar="TIINY_API_KEY", help="API key override.")
def deploy(file, domain, password, bundle, api_key):
    """Deploy a file or zip to a new tiiny.host site."""
    if not domain:
        domain = click.prompt("Choose a subdomain")
    client = _get_client(api_key)

    deploy_file = file
    zip_path = None
    try:
        if bundle:
            with console.status("Bundling..."):
                zip_path = create_bundle(file)
            deploy_file = str(zip_path)

        with console.status("Deploying..."):
            try:
                result = client.create(deploy_file, domain=domain, password=password)
            except TiinyError as e:
                log_event("DEPLOY", domain, success=False, file_path=file, error=e.detail)
                console.print(f"[red]Deploy failed:[/red] {e.detail}")
                raise SystemExit(1)
        data = result.get("data", result)
        link = data.get("link", domain)
        url = f"https://{link}"
        log_event("DEPLOY", domain, success=True, file_path=file, url=url)
        console.print(f"[green]Deployed![/green] {url}")
    finally:
        if zip_path:
            cleanup_bundle(zip_path)


# ── update ───────────────────────────────────────────────────────────────


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--domain", "-d", required=True, help="Subdomain to update.")
@click.option("--password", "-p", default=None, help="Password-protect the site.")
@click.option("--bundle", "-b", is_flag=True, help="Bundle linked local files into a zip.")
@click.option("--api-key", default=None, envvar="TIINY_API_KEY", help="API key override.")
def update(file, domain, password, bundle, api_key):
    """Update an existing tiiny.host site with new content."""
    client = _get_client(api_key)

    update_file = file
    zip_path = None
    try:
        if bundle:
            with console.status("Bundling..."):
                zip_path = create_bundle(file)
            update_file = str(zip_path)

        with console.status("Updating..."):
            try:
                result = client.update(update_file, domain, password=password)
            except TiinyError as e:
                log_event("UPDATE", domain, success=False, file_path=file, error=e.detail)
                console.print(f"[red]Update failed:[/red] {e.detail}")
                raise SystemExit(1)
        data = result.get("data", result)
        link = data.get("link", domain)
        url = f"https://{link}"
        log_event("UPDATE", domain, success=True, file_path=file, url=url)
        console.print(f"[green]Updated![/green] {url}")
    finally:
        if zip_path:
            cleanup_bundle(zip_path)


# ── delete ───────────────────────────────────────────────────────────────


@main.command()
@click.option("--domain", "-d", required=True, help="Subdomain to delete.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@click.option("--api-key", default=None, envvar="TIINY_API_KEY", help="API key override.")
def delete(domain, yes, api_key):
    """Delete a tiiny.host site."""
    if not yes:
        click.confirm(f"Delete site '{domain}'?", abort=True)
    client = _get_client(api_key)
    with console.status("Deleting..."):
        try:
            client.delete(domain)
        except TiinyError as e:
            log_event("DELETE", domain, success=False, error=e.detail)
            console.print(f"[red]Delete failed:[/red] {e.detail}")
            raise SystemExit(1)
    log_event("DELETE", domain, success=True)
    console.print(f"[green]Deleted[/green] {domain}")


# ── list ─────────────────────────────────────────────────────────────────


@main.command(name="list")
@click.option("--api-key", default=None, envvar="TIINY_API_KEY", help="API key override.")
def list_sites(api_key):
    """List all sites and quota usage."""
    client = _get_client(api_key)
    with console.status("Fetching sites..."):
        try:
            data = client.profile()
        except TiinyError as e:
            console.print(f"[red]Failed:[/red] {e.detail}")
            raise SystemExit(1)

    profile_data = data.get("data", data)
    links = profile_data.get("links", [])
    if not links:
        console.print("No sites found.")
        return

    table = Table(title="Your Sites")
    table.add_column("Domain", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Created", style="dim")
    for link in links:
        table.add_row(
            link.get("subdomain", ""),
            link.get("type", ""),
            link.get("created", ""),
        )
    console.print(table)

    max_links = profile_data.get("maxLinks", "?")
    console.print(f"\nQuota: {len(links)}/{max_links} sites used")


# ── profile ──────────────────────────────────────────────────────────────


@main.command()
@click.option("--api-key", default=None, envvar="TIINY_API_KEY", help="API key override.")
def profile(api_key):
    """Show account profile info."""
    client = _get_client(api_key)
    with console.status("Fetching profile..."):
        try:
            data = client.profile()
        except TiinyError as e:
            console.print(f"[red]Failed:[/red] {e.detail}")
            raise SystemExit(1)

    profile_data = data.get("data", data)
    console.print(f"[bold]email:[/bold] {profile_data.get('email', 'N/A')}")
    console.print(f"[bold]sites:[/bold] {len(profile_data.get('links', []))}")
    console.print(f"[bold]max sites:[/bold] {profile_data.get('maxLinks', 'N/A')}")
    console.print(f"[bold]max file size:[/bold] {profile_data.get('maxFileSize', 'N/A')} MB")
    domains = profile_data.get("customDomains", [])
    if domains:
        console.print(f"[bold]domains:[/bold] {', '.join(domains)}")


# ── log ──────────────────────────────────────────────────────────────


@main.command(name="log")
@click.option("-n", "--tail", default=None, type=int, help="Show only the last N entries.")
@click.option("--clear", is_flag=True, help="Clear the deployment log.")
def log_cmd(tail, clear):
    """Show deployment history."""
    if clear:
        clear_log()
        console.print("[green]Log cleared.[/green]")
        return

    lines = read_log(tail=tail)
    if not lines:
        console.print("[dim]No deployment history.[/dim]")
        return

    table = Table(title="Deployment History")
    table.add_column("Timestamp", style="dim")
    table.add_column("Action", style="bold")
    table.add_column("Status")
    table.add_column("Domain", style="cyan")
    table.add_column("File", style="dim")
    table.add_column("Size", style="dim")
    table.add_column("Detail")

    for line in lines:
        parts = line.split("\t")
        # Pad to 7 columns if needed.
        while len(parts) < 7:
            parts.append("")
        timestamp, action, status, domain, file_col, size_col, detail = parts[:7]
        status_styled = (
            f"[green]{status}[/green]" if status == "SUCCESS" else f"[red]{status}[/red]"
        )
        table.add_row(timestamp, action, status_styled, domain, file_col, size_col, detail)

    console.print(table)


# ── config ───────────────────────────────────────────────────────────────


@main.group()
def config():
    """Manage TinyGo configuration."""


@config.command("set-key")
def config_set_key():
    """Interactively set your tiiny.host API key."""
    key = click.prompt("Enter your tiiny.host API key", hide_input=True)
    set_api_key(key.strip())
    console.print("[green]API key saved.[/green]")


@config.command("show")
def config_show():
    """Show current configuration (API key masked)."""
    cfg = get_config()
    key = cfg.get("api_key")
    if key:
        console.print(f"[bold]api_key:[/bold] {mask_key(key)}")
    else:
        console.print("[dim]No API key configured.[/dim]")

    # Show YAML settings (excluding api_key which comes from .env)
    settings = {k: v for k, v in cfg.items() if k != "api_key"}
    if settings:
        for k, v in settings.items():
            console.print(f"[bold]{k}:[/bold] {v}")

    from tinygo.config import ENV_FILE, CONFIG_YAML_FILE
    console.print(f"[bold]secrets path:[/bold] {ENV_FILE}")
    console.print(f"[bold]config path:[/bold] {CONFIG_YAML_FILE}")
