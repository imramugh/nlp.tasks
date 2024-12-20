from typing import Dict, Any, List, Optional
import openai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Task, Project
import json

class ChatProcessor:
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.conversation_history = []

    async def generate_tasks(self, query: str) -> Dict[str, Any]:
        """Generate tasks from a natural language query using ChatGPT."""
        try:
            # Add user query to conversation history
            self.conversation_history.append({"role": "user", "content": query})
            
            # Create system message to format the response
            system_message = {
                "role": "system",
                "content": """You are a helpful task generation assistant that creates structured task lists from user queries.
                When users ask for help or guidance, analyze their request and break it down into clear, actionable tasks.
                
                Consider the following when generating tasks:
                1. Break down complex activities into smaller, manageable tasks
                2. Include both high-level and detailed tasks when appropriate
                3. Assign priorities based on task importance and dependencies
                4. Provide clear, actionable descriptions
                5. Consider the logical order of tasks
                
                You MUST format your response EXACTLY as a JSON object with the following structure:
                {
                    "tasks": [
                        {
                            "title": "Clear, concise task title",
                            "description": "Detailed explanation of what needs to be done and why",
                            "priority": "high|medium|low",
                            "estimated_duration": "in minutes"
                        }
                    ]
                }
                
                Priority Guidelines:
                - high: Critical tasks that block other tasks or are time-sensitive
                - medium: Important tasks that contribute to the goal but aren't blocking
                - low: Nice-to-have tasks or optional enhancements
                
                IMPORTANT: 
                1. Your response MUST be ONLY the JSON object, with no additional text
                2. Make task titles clear and actionable
                3. Provide detailed descriptions that explain both what to do and why
                4. Keep the number of tasks manageable (typically 5-10 tasks)
                5. Ensure all JSON fields are properly formatted strings
                6. For queries asking for advice or steps, convert them into actionable tasks
                7. For queries like 'what are the top things to do', create tasks for each item"""
            }
            
            # Get response from ChatGPT
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    system_message,
                    {"role": "system", "content": "Remember to format your response as a JSON object containing a tasks array, even for general queries like 'what are the top things to do'."},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the response
            try:
                response_content = response.choices[0].message.content.strip()
                
                # Log the raw response for debugging
                print(f"Raw response: {response_content}")
                
                # Ensure the response is valid JSON
                if not response_content.startswith("{"):
                    raise ValueError("Response is not a valid JSON object")
                
                tasks_data = json.loads(response_content)
                
                # Validate the response structure
                if "tasks" not in tasks_data or not isinstance(tasks_data["tasks"], list):
                    raise ValueError("Invalid response structure: missing tasks array")
                
                for task in tasks_data["tasks"]:
                    if not all(k in task for k in ["title", "description", "priority"]):
                        raise ValueError("Invalid task structure: missing required fields")
                    if task["priority"] not in ["low", "medium", "high"]:
                        task["priority"] = "medium"  # Default to medium if invalid
                
                # Add the response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_content
                })
                
                return {
                    "success": True,
                    "response": f"Generated {len(tasks_data['tasks'])} tasks successfully. You can now add these tasks to your project.",
                    "data": tasks_data
                }
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                return {
                    "success": False,
                    "response": f"Failed to parse ChatGPT response: {str(e)}",
                    "data": None
                }
            except ValueError as e:
                print(f"Validation error: {str(e)}")
                return {
                    "success": False,
                    "response": f"Invalid response structure: {str(e)}",
                    "data": None
                }
                
        except Exception as e:
            print(f"General error: {str(e)}")
            return {
                "success": False,
                "response": f"Error generating tasks: {str(e)}",
                "data": None
            }

    async def import_tasks(self, tasks_data: Dict[str, Any], project_name: Optional[str], session: AsyncSession) -> Dict[str, Any]:
        """Import generated tasks into the database."""
        try:
            # If project name is provided, get or create the project
            project = None
            if project_name:
                # Check if project exists
                stmt = select(Project).where(Project.name == project_name)
                result = await session.execute(stmt)
                project = result.scalar_one_or_none()
                
                # Create new project if it doesn't exist
                if not project:
                    project = Project(
                        name=project_name,
                        description=f"Project created for tasks: {project_name}"
                    )
                    session.add(project)
                    await session.flush()

            # Create tasks
            created_tasks = []
            for task_data in tasks_data["tasks"]:
                task = Task(
                    title=task_data["title"],
                    description=task_data.get("description", ""),
                    priority=task_data.get("priority", "medium"),
                    status="pending",
                    project_id=project.project_id if project else None,
                    created_by=1  # Default to test user
                )
                session.add(task)
                created_tasks.append(task)
            
            await session.commit()
            
            # Create success message
            message = f"Successfully imported {len(created_tasks)} tasks"
            if project_name:
                message += f" to project '{project_name}'"
            message += ". You can now view, edit, or manage these tasks."
            
            # Convert tasks to dictionary format
            task_list = []
            for task in created_tasks:
                task_dict = {
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_at": task.created_at.isoformat(),
                    "project_id": task.project_id,
                    "project_name": project_name if project else None,
                    "assigned_to": task.assigned_to,
                    "created_by": task.created_by
                }
                task_list.append(task_dict)
            
            return {
                "success": True,
                "response": message,
                "data": {
                    "tasks": task_list,
                    "project": {"name": project_name, "id": project.project_id} if project else None
                }
            }
            
        except Exception as e:
            await session.rollback()
            return {
                "success": False,
                "response": f"Error importing tasks: {str(e)}",
                "data": None
            }

    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = [] 