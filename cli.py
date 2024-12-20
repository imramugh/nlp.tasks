#!/usr/bin/env python3
import asyncio
import websockets
import json
import click
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich import print as rprint

console = Console()

class TaskManagerCLI:
    def __init__(self, uri="ws://127.0.0.1:8000/ws"):
        self.uri = uri

    async def send_query(self, query: str) -> dict:
        """Send a query to the WebSocket server and return the response."""
        try:
            async with websockets.connect(self.uri) as websocket:
                await websocket.send(query)
                response = await websocket.recv()
                return json.loads(response)
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}", "data": None}

    def display_response(self, response: dict):
        """Display the response in a formatted way."""
        if response["success"]:
            if isinstance(response.get("data"), dict):
                if "tasks" in response["data"]:
                    self.display_tasks_table(response["data"]["tasks"])
                elif "projects" in response["data"]:
                    self.display_projects_table(response["data"]["projects"])
                elif "tables" in response["data"]:
                    self.display_database_schema(response["data"]["tables"])
                else:
                    rprint(Panel(response["response"], title="Success", border_style="green"))
                    if response.get("data"):
                        rprint(response["data"])
            else:
                rprint(Panel(response["response"], title="Success", border_style="green"))
                if response.get("data"):
                    rprint(response["data"])
        else:
            rprint(Panel(response["response"], title="Error", border_style="red"))

    def display_tasks_table(self, tasks: list):
        """Display tasks in a formatted table."""
        table = Table(title="Tasks")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Due Date", style="blue")
        table.add_column("Project", style="cyan")
        table.add_column("Assigned To", style="magenta")

        for task in tasks:
            table.add_row(
                str(task.get("task_id", "")),
                task.get("title", ""),
                task.get("status", ""),
                task.get("priority", ""),
                task.get("due_date", ""),
                str(task.get("project_id", "")),
                str(task.get("assigned_to", ""))
            )

        console.print(table)

    def display_projects_table(self, projects: list):
        """Display projects in a formatted table."""
        table = Table(title="Projects")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Created At", style="blue")

        for project in projects:
            table.add_row(
                str(project.get("project_id", "")),
                project.get("name", ""),
                project.get("description", ""),
                project.get("created_at", "")
            )

        console.print(table)

    def display_database_schema(self, tables: list):
        """Display database schema in a formatted way."""
        for table_info in tables:
            table = Table(title=f"Table: {table_info['name']}", border_style="blue")
            table.add_column("Column", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Nullable", style="green")

            for column in table_info["columns"]:
                table.add_row(
                    column["name"],
                    column["type"],
                    "Yes" if column["nullable"] else "No"
                )

            console.print(table)
            console.print()

@click.group()
def cli():
    """Task Management System CLI"""
    pass

@cli.command()
@click.option('--title', prompt='Task title', help='Title of the task')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high'], case_sensitive=False), prompt=True)
@click.option('--project', help='Project name (optional)')
@click.option('--due', help='Due date (e.g., "tomorrow", "next friday", "2024-01-01")')
@click.option('--assign', help='Username to assign the task to')
def create_task(title, priority, project, due, assign):
    """Create a new task"""
    query = f"Create task '{title}' with {priority} priority"
    if project:
        query += f" for project '{project}'"
    if due:
        query += f" due {due}"
    if assign:
        query += f" and assign to {assign}"
    
    async def run():
        cli = TaskManagerCLI()
        response = await cli.send_query(query)
        cli.display_response(response)
    
    asyncio.run(run())

@cli.command()
@click.option('--priority', type=click.Choice(['low', 'medium', 'high']), help='Filter by priority')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed']), help='Filter by status')
@click.option('--project', help='Filter by project name')
@click.option('--assigned', help='Filter by assigned user')
def list_tasks(priority, status, project, assigned):
    """List tasks with optional filters"""
    query = "Show"
    if priority:
        query += f" {priority} priority"
    if status:
        query += f" {status}"
    query += " tasks"
    if project:
        query += f" in project '{project}'"
    if assigned:
        query += f" assigned to {assigned}"
    
    async def run():
        cli = TaskManagerCLI()
        response = await cli.send_query(query)
        cli.display_response(response)
    
    asyncio.run(run())

@cli.command()
@click.argument('task_id')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed']), help='New status')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high']), help='New priority')
@click.option('--assign', help='Username to assign the task to')
def update_task(task_id, status, priority, assign):
    """Update a task's status, priority, or assignment"""
    if not any([status, priority, assign]):
        click.echo("Please specify at least one attribute to update")
        return
    
    query = f"Update task {task_id}"
    if status:
        query += f" set status to {status}"
    if priority:
        query += f" set priority to {priority}"
    if assign:
        query += f" assign to {assign}"
    
    async def run():
        cli = TaskManagerCLI()
        response = await cli.send_query(query)
        cli.display_response(response)
    
    asyncio.run(run())

@cli.command()
@click.argument('task_id')
def delete_task(task_id):
    """Delete a task"""
    async def run():
        cli = TaskManagerCLI()
        response = await cli.send_query(f"Delete task {task_id}")
        cli.display_response(response)
    
    asyncio.run(run())

@cli.command()
@click.option('--name', prompt='Project name', help='Name of the project')
@click.option('--description', prompt='Project description', help='Description of the project')
def create_project(name, description):
    """Create a new project"""
    async def run():
        cli = TaskManagerCLI()
        response = await cli.send_query(f"Create project '{name}' with description '{description}'")
        cli.display_response(response)
    
    asyncio.run(run())

@cli.command()
def list_projects():
    """List all projects"""
    async def run():
        cli = TaskManagerCLI()
        response = await cli.send_query("Show all projects")
        cli.display_response(response)
    
    asyncio.run(run())

@cli.command()
@click.argument('task_id')
@click.argument('tag_name')
def add_tag(task_id, tag_name):
    """Add a tag to a task"""
    async def run():
        cli = TaskManagerCLI()
        response = await cli.send_query(f"Add tag '{tag_name}' to task {task_id}")
        cli.display_response(response)
    
    asyncio.run(run())

@cli.command()
@click.argument('tag_name')
def list_by_tag(tag_name):
    """List all tasks with a specific tag"""
    async def run():
        cli = TaskManagerCLI()
        response = await cli.send_query(f"Show tasks with tag '{tag_name}'")
        cli.display_response(response)
    
    asyncio.run(run())

@cli.command()
def interactive():
    """Start an interactive session"""
    async def run():
        cli = TaskManagerCLI()
        console.print(Panel.fit("Welcome to Task Manager CLI", border_style="green"))
        console.print("Type 'exit' to quit")
        
        while True:
            query = Prompt.ask("\nEnter your command")
            if query.lower() == 'exit':
                break
            
            response = await cli.send_query(query)
            cli.display_response(response)
    
    asyncio.run(run())

if __name__ == '__main__':
    cli() 