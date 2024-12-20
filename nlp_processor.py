"""
Author: Imran Mughal
Email: imran@mughal.com
Date: December 19, 2024
"""

import openai
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
from sqlalchemy import select, or_, inspect, MetaData, Table
from models import User, Task, Project, Tag
import dateparser
from database_utils import list_tables
from chat_processor import ChatProcessor

class NLPProcessor:
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.chat_processor = ChatProcessor(openai_api_key)

    async def process_query(self, query: str, session) -> Dict[str, Any]:
        """Process natural language query and return structured response."""
        try:
            # Input validation
            if not query or not isinstance(query, str):
                return {
                    "success": False,
                    "response": "Invalid query: Query must be a non-empty string",
                    "data": None
                }

            # Convert query to lowercase for case-insensitive matching
            query_lower = query.lower().strip()

            # Check if this is a bulk task update command
            if query_lower.startswith("for tasks") or query_lower.startswith("set all tasks") or query_lower.startswith("assign all tasks"):
                try:
                    # Extract task IDs and update parameters
                    task_ids = []
                    project_id = None
                    status = None
                    priority = None
                    assigned_to = None

                    # Extract task IDs
                    if query_lower.startswith("set all tasks") or query_lower.startswith("assign all tasks"):
                        # Get all task IDs
                        result = await session.execute(select(Task.task_id))
                        task_ids = [row[0] for row in result.all()]
                    elif "greater than" in query_lower:
                        min_id = int(query_lower.split("greater than")[1].split()[0])
                        result = await session.execute(select(Task.task_id).filter(Task.task_id > min_id))
                        task_ids = [row[0] for row in result.all()]
                    elif "less than" in query_lower:
                        max_id = int(query_lower.split("less than")[1].split()[0])
                        result = await session.execute(select(Task.task_id).filter(Task.task_id < max_id))
                        task_ids = [row[0] for row in result.all()]
                    elif "between" in query_lower:
                        parts = query_lower.split("between")[1].split("and")
                        min_id = int(parts[0].strip())
                        max_id = int(parts[1].split()[0].strip())
                        result = await session.execute(select(Task.task_id).filter(Task.task_id.between(min_id, max_id)))
                        task_ids = [row[0] for row in result.all()]

                    if not task_ids:
                        return {
                            "success": False,
                            "response": "No tasks found matching the specified criteria",
                            "data": None
                        }

                    # Extract update parameters
                    if "set project to" in query_lower or "to project" in query_lower:
                        project_part = query_lower.split("to project")[1].strip() if "to project" in query_lower else query_lower.split("set project to")[1].strip()
                        try:
                            project_id = int(project_part)
                        except ValueError:
                            return {
                                "success": False,
                                "response": f"Invalid project ID: {project_part}",
                                "data": None
                            }
                    elif "set status to" in query_lower:
                        status = query_lower.split("set status to")[1].strip()
                        if status not in ["pending", "in_progress", "completed"]:
                            return {
                                "success": False,
                                "response": f"Invalid status: {status}. Must be one of: pending, in_progress, completed",
                                "data": None
                            }
                    elif "set priority to" in query_lower:
                        priority = query_lower.split("set priority to")[1].strip()
                        if priority not in ["low", "medium", "high"]:
                            return {
                                "success": False,
                                "response": f"Invalid priority: {priority}. Must be one of: low, medium, high",
                                "data": None
                            }
                    elif "assign" in query_lower and "to user" in query_lower:
                        user_id = query_lower.split("to user")[1].strip()
                        try:
                            assigned_to = int(user_id)
                            # Verify user exists
                            result = await session.execute(select(User).filter(User.user_id == assigned_to))
                            user = result.scalar_one_or_none()
                            if not user:
                                return {
                                    "success": False,
                                    "response": f"User with ID {assigned_to} not found",
                                    "data": None
                                }
                        except ValueError:
                            return {
                                "success": False,
                                "response": f"Invalid user ID: {user_id}",
                                "data": None
                            }
                    elif "assign" in query_lower and "to" in query_lower:
                        username = query_lower.split("to")[1].strip()
                        # Find user by username
                        result = await session.execute(select(User).filter(User.username == username))
                        user = result.scalar_one_or_none()
                        if not user:
                            return {
                                "success": False,
                                "response": f"User '{username}' not found",
                                "data": None
                            }
                        assigned_to = user.user_id

                    if not any([project_id is not None, status is not None, priority is not None, assigned_to is not None]):
                        return {
                            "success": False,
                            "response": "No valid update parameters provided",
                            "data": None
                        }

                    params = {"task_ids": task_ids}
                    if project_id is not None:
                        params["project_id"] = project_id
                    if status is not None:
                        params["status"] = status
                    if priority is not None:
                        params["priority"] = priority
                    if assigned_to is not None:
                        params["assigned_to"] = assigned_to

                    result = await self._update_tasks(session, params)
                    return {
                        "success": True,
                        "response": f"Successfully updated {len(task_ids)} tasks.",
                        "data": result
                    }
                except ValueError as e:
                    return {
                        "success": False,
                        "response": f"Error processing bulk update: {str(e)}",
                        "data": None
                    }

            # Check if this is a show tables or schema command
            if query_lower in ["show tables", "show all tables", "show schema"]:
                try:
                    result = await self._list_tables(session)
                    return {
                        "success": True,
                        "response": "Here are the database tables and their schema:",
                        "data": result
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"Error retrieving schema: {str(e)}",
                        "data": None
                    }

            # Check if this is a delete all projects command
            if query_lower in ["delete all projects", "delete all project"]:
                try:
                    result = await self._delete_project(session, {"delete_all": True})
                    return {
                        "success": True,
                        "response": "All projects have been deleted successfully.",
                        "data": result
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"Error deleting projects: {str(e)}",
                        "data": None
                    }

            # Check if this is a delete specific projects command
            if query_lower.startswith("delete project"):
                try:
                    # Extract project IDs from the command
                    parts = query_lower.replace("delete project", "").strip().split(",")
                    project_ids = [int(p.strip()) for p in parts if p.strip().isdigit()]
                    if not project_ids:
                        return {
                            "success": False,
                            "response": "No valid project IDs provided",
                            "data": None
                        }
                    result = await self._delete_project(session, {"project_ids": project_ids})
                    return {
                        "success": True,
                        "response": f"Successfully deleted {result['deleted_projects']} project(s).",
                        "data": result
                    }
                except ValueError as e:
                    return {
                        "success": False,
                        "response": f"Error deleting projects: {str(e)}",
                        "data": None
                    }

            # Check if this is a delete all tasks command
            if query_lower == "delete all tasks":
                try:
                    result = await self._delete_task(session, {"delete_all": True})
                    return {
                        "success": True,
                        "response": "All tasks have been deleted successfully.",
                        "data": result
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"Error deleting tasks: {str(e)}",
                        "data": None
                    }

            # Check if this is a task generation query
            if any(pattern in query_lower for pattern in [
                "how to", "what are the steps", "what do i need to do", "what are the",
                "list the tasks", "create a plan", "break down", "what are",
                "show me how to", "guide me through", "walk me through"
            ]):
                try:
                    result = await self.chat_processor.generate_tasks(query)
                    if result["success"]:
                        return result
                    else:
                        return {
                            "success": False,
                            "response": f"Error generating tasks: {result['response']}",
                            "data": None
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"Error generating tasks: {str(e)}",
                        "data": None
                    }
            
            # Check if this is a task import query
            import_patterns = [
                "add these tasks", "import those tasks", "save these tasks",
                "create these tasks", "add all of these", "import all tasks",
                "save all tasks", "add these to tasks", "add all to tasks",
                "import all", "save all", "add all"
            ]
            if any(pattern in query_lower for pattern in import_patterns) or query_lower in import_patterns:
                try:
                    project_name = None
                    # Extract project name if specified
                    if "to project" in query_lower:
                        parts = query_lower.split("to project")
                        if len(parts) > 1:
                            project_name = parts[1].strip().strip("'\"")
                    
                    # Get the last generated tasks
                    if hasattr(self.chat_processor, "conversation_history") and self.chat_processor.conversation_history:
                        last_response = self.chat_processor.conversation_history[-1]
                        if last_response["role"] == "assistant":
                            try:
                                tasks_data = json.loads(last_response["content"])
                                return await self.chat_processor.import_tasks(tasks_data, project_name, session)
                            except json.JSONDecodeError:
                                return {
                                    "success": False,
                                    "response": "No valid tasks found to import. Please generate tasks first.",
                                    "data": None
                                }
                    return {
                        "success": False,
                        "response": "No tasks found to import. Please generate tasks first.",
                        "data": None
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"Error importing tasks: {str(e)}",
                        "data": None
                    }

            # Handle other operations using GPT-4
            try:
                # Define the system message for other operations
                system_message = """You are a task management system that converts natural language queries into structured database operations.
                Available operations: search_tasks, create_task, update_task, delete_task, create_project, search_projects, list_tables, create_user, search_users.
                
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

                For create_user operation, return parameters in this format:
                {
                    "operation": "create_user",
                    "parameters": {
                        "username": "username",
                        "email": "email@example.com"
                    },
                    "natural_response": "User has been created successfully"
                }

                For search_users operation, return parameters in this format:
                {
                    "operation": "search_users",
                    "parameters": {
                        "username": "username (optional)",
                        "email": "email (optional)"
                    },
                    "natural_response": "Here are the matching users"
                }

                IMPORTANT:
                1. Your response MUST be a valid JSON object with operation, parameters, and natural_response fields
                2. The operation field must be one of the available operations
                3. The parameters must match the format for the specified operation
                4. The natural_response should be a human-readable message describing what was done"""

                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": query}
                    ]
                )

                # Parse the LLM response
                try:
                    response_content = response.choices[0].message.content.strip()
                    
                    # Log the raw response for debugging
                    print(f"Raw response: {response_content}")
                    
                    # Ensure the response is valid JSON
                    if not response_content.startswith("{"):
                        return {
                            "success": False,
                            "response": "Invalid response format: Response must be a JSON object",
                            "data": None
                        }
                    
                    structured_response = json.loads(response_content)
                    
                    # Validate the response structure
                    if "operation" not in structured_response:
                        return {
                            "success": False,
                            "response": "Invalid response structure: missing operation field",
                            "data": None
                        }
                    
                    if "parameters" not in structured_response:
                        return {
                            "success": False,
                            "response": "Invalid response structure: missing parameters field",
                            "data": None
                        }
                    
                    if "natural_response" not in structured_response:
                        return {
                            "success": False,
                            "response": "Invalid response structure: missing natural_response field",
                            "data": None
                        }
                    
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
            except openai.APIError as e:
                return {
                    "success": False,
                    "response": f"OpenAI API error: {str(e)}",
                    "data": None
                }
            
        except Exception as e:
            print(f"Unexpected error in process_query: {str(e)}")
            return {
                "success": False,
                "response": f"Unexpected error: {str(e)}",
                "data": None
            }

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
            return await self._update_task(session, params)
        elif operation == "delete_task":
            return await self._delete_task(session, params)
        elif operation == "create_project":
            return await self._create_project(session, params)
        elif operation == "search_projects":
            return await self._search_projects(session, params)
        elif operation == "list_tables":
            return await self._list_tables(session)
        elif operation == "create_user":
            return await self._create_user(session, params)
        elif operation == "search_users":
            return await self._search_users(session, params)
        else:
            raise ValueError(f"Unknown operation: {operation}")

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

    async def _list_tables(self, session) -> Dict[str, Any]:
        """List all tables in the database with their schema."""
        try:
            # Get the engine from the session
            engine = session.get_bind()
            
            # Create metadata
            metadata = MetaData()
            
            # Get all tables
            tables = [
                {
                    "name": "tasks",
                    "columns": [
                        {"name": "task_id", "type": "INTEGER", "nullable": False},
                        {"name": "title", "type": "VARCHAR", "nullable": False},
                        {"name": "description", "type": "TEXT", "nullable": True},
                        {"name": "status", "type": "VARCHAR", "nullable": False},
                        {"name": "priority", "type": "VARCHAR", "nullable": False},
                        {"name": "due_date", "type": "DATETIME", "nullable": True},
                        {"name": "created_at", "type": "DATETIME", "nullable": False},
                        {"name": "project_id", "type": "INTEGER", "nullable": True},
                        {"name": "assigned_to", "type": "INTEGER", "nullable": True},
                        {"name": "created_by", "type": "INTEGER", "nullable": False}
                    ]
                },
                {
                    "name": "projects",
                    "columns": [
                        {"name": "project_id", "type": "INTEGER", "nullable": False},
                        {"name": "name", "type": "VARCHAR", "nullable": False},
                        {"name": "description", "type": "TEXT", "nullable": True},
                        {"name": "created_at", "type": "DATETIME", "nullable": False}
                    ]
                },
                {
                    "name": "users",
                    "columns": [
                        {"name": "user_id", "type": "INTEGER", "nullable": False},
                        {"name": "username", "type": "VARCHAR", "nullable": False},
                        {"name": "email", "type": "VARCHAR", "nullable": False},
                        {"name": "created_at", "type": "DATETIME", "nullable": False}
                    ]
                },
                {
                    "name": "tags",
                    "columns": [
                        {"name": "tag_id", "type": "INTEGER", "nullable": False},
                        {"name": "name", "type": "VARCHAR", "nullable": False},
                        {"name": "created_by", "type": "INTEGER", "nullable": False}
                    ]
                },
                {
                    "name": "task_tags",
                    "columns": [
                        {"name": "task_id", "type": "INTEGER", "nullable": False},
                        {"name": "tag_id", "type": "INTEGER", "nullable": False}
                    ]
                }
            ]
            
            return {"tables": tables}
            
        except Exception as e:
            print(f"Error in _list_tables: {str(e)}")
            raise ValueError(f"Error listing tables: {str(e)}")

    async def _search_tasks(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search tasks based on various criteria."""
        try:
            query = select(Task, Project).outerjoin(Project, Task.project_id == Project.project_id)
            
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
            tasks_with_projects = result.all()
            return {
                "tasks": [
                    {
                        **self._task_to_dict(task),
                        "project_name": project.name if project else None
                    }
                    for task, project in tasks_with_projects
                ]
            }
        except Exception as e:
            raise ValueError(f"Error searching tasks: {str(e)}")

    async def _create_task(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        try:
            # Get or create project if project name is provided
            project_id = params.get("project_id")
            project_name = None
            if isinstance(project_id, str):
                # If project_id is a string, treat it as a project name
                project_name = project_id
                result = await session.execute(select(Project).filter(Project.name == project_name))
                project = result.scalar_one_or_none()
                if not project:
                    # Create new project
                    project = Project(
                        name=project_name,
                        description=f"Project created for task: {params['title']}"
                    )
                    session.add(project)
                    await session.flush()
                project_id = project.project_id

            task = Task(
                title=params["title"],
                description=params.get("description"),
                status=params.get("status", "pending"),
                priority=params.get("priority", "medium"),
                due_date=params.get("due_date"),
                project_id=project_id,
                created_by=params.get("created_by", 1)  # Default to test user if not specified
            )
            session.add(task)
            await session.flush()
            
            # Get project name if project_id is set
            if task.project_id and not project_name:
                result = await session.execute(select(Project).filter(Project.project_id == task.project_id))
                project = result.scalar_one_or_none()
                project_name = project.name if project else None
            
            task_dict = self._task_to_dict(task)
            task_dict["project_name"] = project_name
            return task_dict
        except KeyError as e:
            raise ValueError(f"Missing required parameter: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error creating task: {str(e)}")

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
        except Exception as e:
            raise ValueError(f"Error creating project: {str(e)}")

    async def _update_task(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task."""
        try:
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
                        value = self._parse_date(value)
                    setattr(task, field, value)

            await session.flush()
            return self._task_to_dict(task)
        except Exception as e:
            raise ValueError(f"Error updating task: {str(e)}")

    async def _delete_task(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a task or all tasks."""
        try:
            if params.get("delete_all", False):
                # Delete all tasks
                result = await session.execute(select(Task))
                tasks = result.scalars().all()
                for task in tasks:
                    await session.delete(task)
                await session.flush()
                return {"deleted_tasks": len(tasks)}
            else:
                # Delete a single task
                task_id = params.get("task_id")
                if not task_id:
                    raise ValueError("Task ID is required for delete operation")

                result = await session.execute(select(Task).filter(Task.task_id == task_id))
                task = result.scalar_one_or_none()
                if not task:
                    raise ValueError(f"Task with ID {task_id} not found")

                await session.delete(task)
                await session.flush()
                return {"deleted_task_id": task_id}
        except Exception as e:
            raise ValueError(f"Error deleting task(s): {str(e)}")

    async def _search_projects(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search projects."""
        try:
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
        except Exception as e:
            raise ValueError(f"Error searching projects: {str(e)}")

    async def _delete_project(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a project or all projects."""
        try:
            if params.get("delete_all", False):
                # Delete all projects
                result = await session.execute(select(Project))
                projects = result.scalars().all()
                for project in projects:
                    await session.delete(project)
                await session.flush()
                return {"deleted_projects": len(projects)}
            else:
                # Delete specific projects
                project_ids = params.get("project_ids", [])
                if not project_ids:
                    raise ValueError("Project ID(s) required for delete operation")

                deleted_count = 0
                for project_id in project_ids:
                    result = await session.execute(select(Project).filter(Project.project_id == project_id))
                    project = result.scalar_one_or_none()
                    if project:
                        await session.delete(project)
                        deleted_count += 1

                await session.flush()
                return {"deleted_projects": deleted_count}
        except Exception as e:
            raise ValueError(f"Error deleting project(s): {str(e)}")

    async def _update_tasks(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update multiple tasks."""
        try:
            task_ids = params.get("task_ids", [])
            if not task_ids:
                raise ValueError("Task IDs are required for bulk update operation")

            # Get all tasks
            result = await session.execute(select(Task).filter(Task.task_id.in_(task_ids)))
            tasks = result.scalars().all()
            if not tasks:
                raise ValueError(f"No tasks found with IDs {task_ids}")

            # Update all tasks
            for task in tasks:
                for field, value in params.items():
                    if field != "task_ids" and hasattr(task, field):
                        if field == "due_date" and value:
                            value = self._parse_date(value)
                        setattr(task, field, value)

            await session.flush()
            return {
                "updated_tasks": [self._task_to_dict(task) for task in tasks]
            }
        except Exception as e:
            raise ValueError(f"Error updating tasks: {str(e)}")

    async def _create_user(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        try:
            user = User(
                username=params["username"],
                email=params["email"]
            )
            session.add(user)
            await session.flush()
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat()
            }
        except KeyError as e:
            raise ValueError(f"Missing required parameter: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error creating user: {str(e)}")

    async def _search_users(self, session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search users."""
        try:
            query = select(User)
            result = await session.execute(query)
            users = result.scalars().all()
            return {
                "users": [
                    {
                        "user_id": u.user_id,
                        "username": u.username,
                        "email": u.email,
                        "created_at": u.created_at.isoformat()
                    }
                    for u in users
                ]
            }
        except Exception as e:
            raise ValueError(f"Error searching users: {str(e)}") 