"""
Central UI module for Rich TUI integration.
"""
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich import box

# Define custom theme
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "success": "bold green",
    "user": "bold yellow",
    "bot": "bold cyan",
    "highlight": "bold magenta",
})

# Global Console instance
console = Console(theme=custom_theme, legacy_windows=False)

def print_banner(text, style="blue"):
    """Prints a styled banner text (Borderless)."""
    console.print(Text(text, justify="center", style=style))
    # console.print(Rule(style=style)) # User requested removing lines

def print_error(text):
    """Prints an error message."""
    console.print(f"[bold red]❌ {text}[/bold red]")

def print_success(text):
    """Prints a success message."""
    console.print(f"[bold green]✅ {text}[/bold green]")

def print_info(text):
    """Prints an info message."""
    console.print(f"[dim cyan]ℹ️ {text}[/dim cyan]")

def print_warning(text):
    """Prints a warning message."""
    console.print(f"[bold magenta]⚠️ {text}[/bold magenta]")
