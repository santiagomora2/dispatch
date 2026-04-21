import typer
from agent.agent import run

app = typer.Typer()

@app.command()
def main():
    # Run the agent
    run()

if __name__ == "__main__":
    app()