#!/usr/bin/env python3
"""
CLI principal do AI-Dev.
"""
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
import uvicorn

# Adicionar o diretório atual ao Python path
sys.path.insert(0, str(Path(__file__).parent))

console = Console()
app = typer.Typer(
    name="ai-dev",
    help="IA Engenheira de Software - Ferramenta para desenvolvimento automatizado",
    rich_markup_mode="rich"
)


@app.command()
def plan(
    task: str = typer.Argument(..., help="Descrição da tarefa"),
    repo: str = typer.Option(".", "--repo", help="Caminho do repositório"),
    max_iters: int = typer.Option(5, "--max-iters", help="Máximo de iterações"),
    output: Optional[str] = typer.Option(None, "--output", help="Arquivo de saída do plano")
):
    """Planeja uma tarefa sem executar."""
    console.print(f"[blue]Planejando tarefa:[/blue] {task}")
    console.print(f"[blue]Repositório:[/blue] {repo}")
    
    try:
        from agent.planner import AgentPlanner
        
        planner = AgentPlanner()
        plan = planner.plan_task(task, repo, max_iters, dry_run=True)
        
        console.print("\n[green]Plano gerado:[/green]")
        console.print(plan)
        
        if output:
            with open(output, "w") as f:
                f.write(plan)
            console.print(f"\n[green]Plano salvo em:[/green] {output}")
            
    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def fix(
    task: str = typer.Argument(..., help="Descrição da tarefa"),
    repo: str = typer.Option(".", "--repo", help="Caminho do repositório"),
    max_iters: int = typer.Option(5, "--max-iters", help="Máximo de iterações"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Apenas planejar")
):
    """Corrige um bug ou problema."""
    console.print(f"[blue]Corrigindo:[/blue] {task}")
    console.print(f"[blue]Repositório:[/blue] {repo}")
    
    try:
        from agent.planner import AgentPlanner
        
        planner = AgentPlanner()
        result = planner.run_task(task, repo, max_iters, dry_run)
        
        console.print("\n[green]Resultado:[/green]")
        console.print(result)
        
    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def implement(
    task: str = typer.Argument(..., help="Descrição da funcionalidade"),
    repo: str = typer.Option(".", "--repo", help="Caminho do repositório"),
    max_iters: int = typer.Option(5, "--max-iters", help="Máximo de iterações"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Apenas planejar"),
    apply: bool = typer.Option(False, "--apply", help="Aplicar mudanças")
):
    """Implementa uma nova funcionalidade."""
    console.print(f"[blue]Implementando:[/blue] {task}")
    console.print(f"[blue]Repositório:[/blue] {repo}")
    
    try:
        from agent.planner import AgentPlanner
        
        planner = AgentPlanner()
        result = planner.run_task(task, repo, max_iters, dry_run and not apply)
        
        console.print("\n[green]Resultado:[/green]")
        console.print(result)
        
    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def index(
    repo: str = typer.Option(".", "--repo", help="Caminho do repositório"),
    rebuild: bool = typer.Option(False, "--rebuild", help="Recriar índice")
):
    """Indexa um repositório no banco de vetores."""
    console.print(f"[blue]Indexando repositório:[/blue] {repo}")
    
    try:
        from agent.memory.indexer import index_repository
        
        result = index_repository(repo, rebuild)
        
        table = Table(title="Resultado da Indexação")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Repositório", result["repo_path"])
        table.add_row("Total de arquivos", str(result["total_files"]))
        table.add_row("Indexados", str(result["indexed"]))
        table.add_row("Falharam", str(result["failed"]))
        table.add_row("Sucesso", "✅" if result["success"] else "❌")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


# Subcomando para treinamento
train_app = typer.Typer(name="train", help="Comandos de treinamento")
app.add_typer(train_app)


@train_app.command("sft")
def train_sft(
    train_file: str = typer.Option("data/sft_train.jsonl", "--train", help="Arquivo de treino"),
    eval_file: str = typer.Option("data/sft_eval.jsonl", "--eval", help="Arquivo de avaliação"),
    output_dir: str = typer.Option("out-lora", "--output", help="Diretório de saída"),
    epochs: int = typer.Option(2, "--epochs", help="Número de épocas")
):
    """Treina modelo com SFT (LoRA)."""
    console.print("[blue]Iniciando treinamento SFT...[/blue]")
    
    try:
        from training.finetune_lora import train_sft_model
        
        result = train_sft_model(train_file, eval_file, output_dir, epochs)
        console.print(f"[green]Treinamento concluído:[/green] {result}")
        
    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@train_app.command("dpo")
def train_dpo(
    data_file: str = typer.Option("data/dpo_train.jsonl", "--data", help="Arquivo de dados DPO"),
    output_dir: str = typer.Option("out-dpo", "--output", help="Diretório de saída"),
    epochs: int = typer.Option(1, "--epochs", help="Número de épocas")
):
    """Treina modelo com DPO."""
    console.print("[blue]Iniciando treinamento DPO...[/blue]")
    
    try:
        from training.dpo_train import train_dpo_model
        
        result = train_dpo_model(data_file, output_dir, epochs)
        console.print(f"[green]Treinamento concluído:[/green] {result}")
        
    except Exception as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def api(
    host: str = typer.Option("0.0.0.0", "--host", help="Host do servidor"),
    port: int = typer.Option(8000, "--port", help="Porta do servidor"),
    reload: bool = typer.Option(False, "--reload", help="Recarregar automaticamente"),
    workers: int = typer.Option(1, "--workers", help="Número de workers")
):
    """Inicia o servidor API."""
    console.print(f"[blue]Iniciando API em[/blue] http://{host}:{port}")
    console.print("[yellow]Pressione Ctrl+C para parar[/yellow]")
    
    try:
        uvicorn.run(
            "api.server:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="info"
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Servidor parado[/yellow]")


@app.command()
def status():
    """Mostra status do sistema."""
    console.print("[blue]Status do AI-Dev[/blue]")
    
    table = Table(title="Configuração Atual")
    table.add_column("Componente", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Configuração", style="yellow")
    
    # LLM Backend
    llm_backend = os.getenv("LLM_BACKEND", "openai")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    table.add_row("LLM Backend", "✅", f"{llm_backend} ({llm_model})")
    
    # Vector Backend
    vector_backend = os.getenv("VECTOR_BACKEND", "qdrant")
    table.add_row("Vector DB", "✅", vector_backend)
    
    # Sandbox
    sandbox_image = os.getenv("SANDBOX_IMAGE", "python:3.11-slim")
    table.add_row("Sandbox", "✅", sandbox_image)
    
    console.print(table)


if __name__ == "__main__":
    app()
