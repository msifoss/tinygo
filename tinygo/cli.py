"""TinyGo CLI — deploy web pages to tiiny.host."""

import click
from rich.console import Console
from rich.table import Table

from tinygo.api import TiinyClient, TiinyError
from tinygo.config import get_api_key, get_config, mask_key, set_api_key

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
@click.option("--api-key", default=None, envvar="TIINY_API_KEY", help="API key override.")
def deploy(file, domain, password, api_key):
    """Deploy a file or zip to a new tiiny.host site."""
    if not domain:
        domain = click.prompt("Choose a subdomain")
    client = _get_client(api_key)
    with console.status("Deploying..."):
        try:
            result = client.create(file, domain=domain, password=password)
        except TiinyError as e:
            console.print(f"[red]Deploy failed:[/red] {e.detail}")
            raise SystemExit(1)
    data = result.get("data", result)
    link = data.get("link", domain)
    console.print(f"[green]Deployed![/green] https://{link}")


# ── update ───────────────────────────────────────────────────────────────


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--domain", "-d", required=True, help="Subdomain to update.")
@click.option("--password", "-p", default=None, help="Password-protect the site.")
@click.option("--api-key", default=None, envvar="TIINY_API_KEY", help="API key override.")
def update(file, domain, password, api_key):
    """Update an existing tiiny.host site with new content."""
    client = _get_client(api_key)
    with console.status("Updating..."):
        try:
            result = client.update(file, domain, password=password)
        except TiinyError as e:
            console.print(f"[red]Update failed:[/red] {e.detail}")
            raise SystemExit(1)
    data = result.get("data", result)
    link = data.get("link", domain)
    console.print(f"[green]Updated![/green] https://{link}")


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
            console.print(f"[red]Delete failed:[/red] {e.detail}")
            raise SystemExit(1)
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
    from tinygo.config import CONFIG_FILE
    console.print(f"[bold]config path:[/bold] {CONFIG_FILE}")
