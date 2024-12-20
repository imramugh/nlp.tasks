import openai
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
from sqlalchemy import select, or_, inspect
from models import User, Task, Project, Tag
import dateparser

class NLPProcessor:
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)

    async def process_query(self, query: str, session) -> Dict[str, Any]:
        """Process natural language query and return structured response."""
        try:
            # Define the system message for the LLM
            system_message = """You are a task management system that converts natural language queries into structured database operations.
            Available operations: search_tasks, create_task, update_task, delete_task, create_project, search_projects, list_tables.
            
            For create_task operation, return parameters in this format:
            {
                "operation": "create_task",
                "parameters": {
                    "title": "task title",
                    "description": "task description (optional)",
                    "priority": "high/medium/low",
                    "due_date": "YYYY-MM-DD HH:mm:ss" or natural language date,
                    "created_by": 1
                },
                "natural_response": "Human readable response"
            }
            
            For update_task operation, return parameters in this format:
            {
                "operation": "update_task",
                "parameters": {
                    "task_id": 123,
                    "status": "pending/in_progress/completed (optional)",
                    "priority": "high/medium/low (optional)",
                    "due_date": "YYYY-MM-DD HH:mm:ss" or natural language date (optional),
                    "assigned_to": user_id (optional),
                    "project_id": project_id (optional),
                    "title": "new title (optional)",
                    "description": "new description (optional)"
                },
                "natural_response": "Human readable response"
            }
            
            For create_project operation, return parameters in this format:
            {
                "operation": "create_project",
                "parameters": {
                    "name": "project name",
                    "description": "project description"
                },
                "natural_response": "Human readable response"
            }
            
            For search_projects operation, return parameters in this format:
            {
                "operation": "search_projects",
                "parameters": {},
                "natural_response": "Here are all projects"
            }

            For list_tables operation, return parameters in this format:
            {
                "operation": "list_tables",
                "parameters": {},
                "natural_response": "Here are all available tables"
            }

            For search_tasks operation, return parameters in this format:
            {
                "operation": "search_tasks",
                "parameters": {
                    "status": "pending/in_progress/completed (optional)",
                    "priority": "high/medium/low (optional)",
                    "search_term": "search term (optional)"
                },
                "natural_response": "Human readable response"
            }
            
            When processing update commands like "set task 2 project to 1", make sure to:
            1. Extract the task_id (2 in this case)
            2. Identify the field being updated (project_id in this case)
            3. Extract the new value (1 in this case)
            4. Return an update_task operation with the correct parameters
            """

            # Get LLM response
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": query}
                    ]
                )
            except openai.APIError as e:
                return {
                    "success": False,
                    "response": f"OpenAI API error: {str(e)}",
                    "data": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"Error calling OpenAI API: {str(e)}",
                    "data": None
                }

            # Parse the LLM response
            try:
                structured_response = json.loads(response.choices[0].message.content)
                result = await self._execute_operation(structured_response, session)
                return {
                    "success": True,
                    "response": structured_response["natural_response"],
                    "data": result
                }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "response": f"Error processing the request: Invalid response format - {str(e)}",
                    "data": None
                }
            except KeyError as e:
                return {
                    "success": False,
                    "response": f"Missing required field in response: {str(e)}",
                    "data": None
                }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"Error processing response: {str(e)}",
                    "data": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "response": f"Unexpected error: {str(e)}",
                "data": None
            }

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse a date string into a datetime object."""
        if not date_str:
            return None
        
        try:
            parsed_date = dateparser.parse(date_str, settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': datetime.now()
            })
            
            if not parsed_date:
                raise ValueError(f"Could not parse date: {date_str}")
            
            return parsed_date
        except Exception as e:
            raise ValueError(f"Error parsing date '{date_str}': {str(e)}")

    async def _execute_operation(self, structured_response: Dict[str, Any], session) -> Optional[Dict[str, Any]]:
        """Execute the database operation based on the structured response."""
        operation = structured_response["operation"]
        params = structured_response["parameters"]

        if operation == "search_tasks":
            return await self._search_tasks(session, params)
        elif operation == "create_task":
            if "due_date" in params:
                params["due_date"] = self._parse_date(params["due_date"])
            return await self._create_task(session, params)
        elif operation == "update_task":
            task_id = params.get("task_id")
            if not task_id:
                raise ValueError("Task ID is required for update operation")
            return await self._process_update_task(session, task_id, params)
        elif operation == "delete_task":
            return await self._delete_task(session, params)
        elif operation == "create_project":
            return await self._create_project(session, params)
        elif operation == "search_projects":
            return await self._search_projects(session, params)
        elif operation == "list_tables":
            return await self._list_tables(session)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _search_tasks(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search tasks based on various criteria."""
        query = select(Task)
        
        if "status" in params:
            query = query.filter(Task.status == params["status"])
        if "priority" in params:
            query = query.filter(Task.priority == params["priority"])
        if "search_term" in params:
            search_term = f"%{params['search_term']}%"
            query = query.filter(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            )

        result = await session.execute(query)
        tasks = result.scalars().all()
        return {"tasks": [self._task_to_dict(task) for task in tasks]}

    async def _create_task(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        try:
            task = Task(
                title=params["title"],
                description=params.get("description"),
                status=params.get("status", "pending"),
                priority=params.get("priority", "medium"),
                due_date=params.get("due_date"),
                created_by=params.get("created_by", 1)  # Default to test user if not specified
            )
            session.add(task)
            await session.flush()
            return self._task_to_dict(task)
        except KeyError as e:
            raise ValueError(f"Missing required parameter: {str(e)}")

    async def _create_project(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project."""
        try:
            project = Project(
                name=params["name"],
                description=params.get("description", "")
            )
            session.add(project)
            await session.flush()
            return {
                "project_id": project.project_id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat()
            }
        except KeyError as e:
            raise ValueError(f"Missing required parameter: {str(e)}")

    async def _update_task(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task."""
        task_id = params.get("task_id")
        if not task_id:
            raise ValueError("Task ID is required for update operation")

        result = await session.execute(select(Task).filter(Task.task_id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")

        # Update all provided fields
        for field, value in params.items():
            if field != "task_id" and hasattr(task, field):
                if field == "due_date" and value:
                    task.due_date = self._parse_date(value)
                else:
                    setattr(task, field, value)

        await session.flush()
        return self._task_to_dict(task)

    async def _process_update_task(self, session, task_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Process task updates with natural language parameters."""
        params = {"task_id": task_id}
        
        if "status" in updates:
            params["status"] = updates["status"]
        if "priority" in updates:
            params["priority"] = updates["priority"]
        if "due_date" in updates:
            params["due_date"] = updates["due_date"]
        if "assigned_to" in updates:
            params["assigned_to"] = updates["assigned_to"]
        if "project_id" in updates:
            params["project_id"] = updates["project_id"]
        if "title" in updates:
            params["title"] = updates["title"]
        if "description" in updates:
            params["description"] = updates["description"]
            
        return await self._update_task(session, params)

    async def _delete_task(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a task."""
        task_id = params.get("task_id")
        if not task_id:
            raise ValueError("Task ID is required for delete operation")

        result = await session.execute(select(Task).filter(Task.task_id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")

        await session.delete(task)
        return {"deleted_task_id": task_id}

    async def _search_projects(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search projects."""
        query = select(Project)
        result = await session.execute(query)
        projects = result.scalars().all()
        return {
            "projects": [
                {
                    "project_id": p.project_id,
                    "name": p.name,
                    "description": p.description,
                    "created_at": p.created_at.isoformat()
                }
                for p in projects
            ]
        }

    async def _list_tables(self, session) -> Dict[str, Any]:
        """List all tables in the database."""
        inspector = inspect(session.get_bind())
        tables = inspector.get_table_names()
        return {
            "tables": [
                {
                    "name": table,
                    "columns": [
                        {
                            "name": column["name"],
                            "type": str(column["type"]),
                            "nullable": column["nullable"]
                        }
                        for column in inspector.get_columns(table)
                    ]
                }
                for table in tables
            ]
        }

    @staticmethod
    def _task_to_dict(task: Task) -> Dict[str, Any]:
        """Convert a Task object to a dictionary."""
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat(),
            "project_id": task.project_id,
            "assigned_to": task.assigned_to,
            "created_by": task.created_by
        } 