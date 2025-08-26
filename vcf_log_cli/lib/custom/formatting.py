from rich.progress import Progress, SpinnerColumn, TextColumn

def beautifyHeader(text):
    header="\n=============================================================\n"+text+"\n=============================================================\n"
    return header

def withLoader(description):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Progress(SpinnerColumn(),
                          TextColumn("[progress.description]{task.description}"),
                          transient=True,) as progress:
                progress.add_task(description=description, total=None)
                value = None
                valie = func(*args, **kwargs)
            return value
        return wrapper
    return decorator

class FormatCodes:
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    @staticmethod
    def title(input_string):
        text = f"[cyan][bold]  {input_string.upper()} [/cyan][/bold]"
        header=f"[cyan][bold]\n=================================\n{text}\n=================================\n[/cyan][/bold]"
        return header

    @staticmethod
    def subtitle(input_string):
        text = f"\n[cyan] -- {input_string} -- [/cyan]"
        return text
    
    @staticmethod
    def fail(input_string):
        text = f"[red]{input_string}[/red]"
        # text = typer.style(input_string, fg=typer.colors.RED)
        return text
    
    @staticmethod
    def success(input_string):
        # text = typer.style(input_string, fg=typer.colors.GREEN)
        text = f"[green]{input_string}[/green]"
        return text
    
    @staticmethod
    def info(input_string):
        text = f"[blue]{input_string}[/blue]"
        return text