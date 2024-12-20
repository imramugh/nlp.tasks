#!/usr/bin/env python3

"""
Author: Imran Mughal
Email: imran@mughal.com
Date: December 19, 2024
"""

import asyncio
import websockets
import json
import click
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import logging

# Suppress websockets and asyncio logging
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)

# Configure minimal console output
console = Console(stderr=False)

class TaskManagerCLI:
    def __init__(self, uri="ws://127.0.0.1:8000/ws"):
        self.uri = uri

    async def send_query(self, query: str) -> dict:
        """Send a query to the WebSocket server and return the response."""
        try:
            async with websockets.connect(self.uri, logger=None) as websocket:
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
                    console.print(response["response"], style="green")
                    if response.get("data"):
                        console.print(response["data"])
            else:
                console.print(response["response"], style="green")
                if response.get("data"):
                    console.print(response["data"])
        else:
            console.print(f"Error: {response['response']}", style="red")

    def display_tasks_table(self, tasks: list):
        """Display tasks in a formatted table."""
        if not tasks:
            console.print("No tasks found.", style="yellow")
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")
        table.add_column("Priority", style="yellow")
        table.add_column("Due Date", style="blue")
        table.add_column("Project", style="cyan")
        table.add_column("Assigned To", style="magenta")

        for task in tasks:
            table.add_row(
                str(task.get("task_id", "")),
                task.get("title", ""),
                task.get("description", "")[:50] + "..." if task.get("description", "") and len(task.get("description", "")) > 50 else task.get("description", ""),
                task.get("status", ""),
                task.get("priority", ""),
                task.get("due_date", ""),
                task.get("project_name", "None"),
                str(task.get("assigned_to", ""))
            )

        console.print(table)
        console.print(f"\nTotal tasks: {len(tasks)}", style="blue")

    def display_projects_table(self, projects: list):
        """Display projects in a formatted table."""
        if not projects:
            console.print("No projects found.", style="yellow")
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
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
        console.print(f"\nTotal projects: {len(projects)}", style="blue")

    def display_database_schema(self, tables: list):
        """Display database schema in a formatted table."""
        if not tables:
            console.print("No tables found.", style="yellow")
            return

        for table_info in tables:
            schema_table = Table(
                title=f"Table: {table_info['name']}", 
                show_header=True, 
                header_style="bold cyan"
            )
            schema_table.add_column("Column Name", style="white")
            schema_table.add_column("Type", style="green")
            schema_table.add_column("Nullable", style="yellow")

            for column in table_info["columns"]:
                schema_table.add_row(
                    column["name"],
                    str(column["type"]),
                    "Yes" if column.get("nullable", True) else "No"
                )

            console.print(schema_table)
            console.print()

@click.group()
def cli():
    """Task Management System CLI"""
    pass

@cli.command()
def interactive():
    """Start an interactive session"""
    async def run():
        cli = TaskManagerCLI()
        
        while True:
            try:
                query = Prompt.ask("\nEnter your command")
                if query.lower() in ['exit', 'quit']:
                    break
                
                # Special handling for delete all tasks
                if query.lower() in ['delete all tasks', 'remove all tasks']:
                    confirm = Prompt.ask("Are you sure you want to delete all tasks? (yes/no)")
                    if confirm.lower() != 'yes':
                        console.print("Operation cancelled.", style="yellow")
                        continue
                
                response = await cli.send_query(query)
                cli.display_response(response)
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"Error: {str(e)}", style="red")
    
    asyncio.run(run())

if __name__ == '__main__':
    cli() 