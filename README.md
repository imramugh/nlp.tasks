# Natural Language Task Management System

A modern task management system that allows users to interact with tasks using natural language through a WebSocket interface. Built with FastAPI, SQLite, and OpenAI's GPT for natural language processing.

## Features

- Natural language interface for task management
- Real-time communication via WebSocket
- Task organization by projects and tags
- Priority and status tracking
- Due date management
- User assignment capabilities

## Prerequisites

- Python 3.8+
- OpenAI API key
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd task-management
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```

5. Add your OpenAI API key to the `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Setup

1. Create a test user:
```bash
python create_test_user.py
```

2. Start the server:
```bash
python main.py
```

The server will start at `http://localhost:8000`.

## Usage

### WebSocket Connection

You can interact with the system using natural language through a WebSocket connection at `ws://localhost:8000/ws`.

### Example Natural Language Commands

1. **Creating Tasks**
   - "Create a new task called 'Review documentation' with high priority"
   - "Add a task 'Update website' due tomorrow"
   - "Create a task 'Team meeting' for project 'Marketing' due next Monday"

2. **Viewing Tasks**
   - "Show me all my tasks"
   - "What are my high priority tasks?"
   - "Show tasks due this week"
   - "List all tasks in project 'Marketing'"
   - "Show me all tasks assigned to John"

3. **Updating Tasks**
   - "Mark task 'Review documentation' as completed"
   - "Change priority of task 'Update website' to high"
   - "Assign task 'Team meeting' to Sarah"
   - "Move task 'Bug fix' to project 'Backend'"

4. **Deleting Tasks**
   - "Delete task 'Old meeting'"
   - "Remove all completed tasks"

5. **Working with Tags**
   - "Add tag 'urgent' to task 'Server maintenance'"
   - "Show all tasks with tag 'bug'"
   - "Remove tag 'urgent' from task 'Update docs'"

6. **Project Management**
   - "Create project 'Website Redesign'"
   - "Show all projects"
   - "List tasks in project 'Marketing Campaign'"

### REST API Endpoints

The system also provides REST API endpoints:

- `GET /health` - Check server health
- `POST /tasks` - Create a new task directly via REST API

### Command Line Interface (CLI)

The system provides a powerful CLI for managing tasks. You can use it in two modes:

1. **Command Mode** - Execute specific commands with arguments
2. **Interactive Mode** - Enter natural language commands interactively

#### Basic Commands

```bash
# Show help
python cli.py --help

# Create a new task
python cli.py create-task --title "Review code" --priority high --due "tomorrow" --project "Backend"

# List tasks with filters
python cli.py list-tasks --priority high --status pending
python cli.py list-tasks --project "Backend" --assigned "testuser"

# Update a task
python cli.py update-task 1 --status completed --priority high
python cli.py update-task 2 --assign "testuser"

# Delete a task
python cli.py delete-task 1

# Project management
python cli.py create-project --name "New Website" --description "Company website redesign"
python cli.py list-projects

# Tag management
python cli.py add-tag 1 "urgent"
python cli.py list-by-tag "urgent"

# Start interactive mode
python cli.py interactive
```

#### Interactive Mode

In interactive mode, you can enter natural language commands directly:

```bash
$ python cli.py interactive

Welcome to Task Manager CLI
Type 'exit' to quit

> Create a task "Review PR" with high priority due tomorrow
Task created successfully!

> Show all my high priority tasks
[Table with tasks will be displayed]

> Mark task 1 as completed
Task updated successfully!

> exit
```

#### CLI Features

- Rich text formatting and colored output
- Interactive prompts for required information
- Table-formatted task listings
- Error handling with clear messages
- Command history in interactive mode
- Tab completion for commands
- Help text for all commands

## Database Schema

The system uses SQLite with the following main tables:
- `users` - User management
- `projects` - Project organization
- `tasks` - Task details and metadata
- `tags` - User-defined tags
- `task_tags` - Task-tag relationships

## Testing

You can test the system using the provided test client:

```bash
python test_client.py
```

This will run a series of test queries to demonstrate the system's capabilities.

## Example WebSocket Client Code

```python
import asyncio
import websockets
import json

async def send_query(query: str):
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        await websocket.send(query)
        response = await websocket.recv()
        return json.loads(response)

# Example usage
async def main():
    response = await send_query("Create a task 'Test WebSocket' with high priority")
    print(response)

asyncio.run(main())
```

## Error Handling

The system provides clear error messages when:
- The natural language query cannot be understood
- Required information is missing
- Database operations fail
- Invalid operations are requested

## Security Considerations

- The system uses environment variables for sensitive information
- CORS is configured to restrict access in production
- Database operations are protected against SQL injection
- Input is validated and sanitized

## Future Enhancements

- Task comments system
- File attachments
- Task dependencies
- Recurring tasks
- Team/Group management
- Task history/audit log

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 

## WebSocket Examples

### Python WebSocket Client

Here's a complete example showing how to interact with the task management system using WebSocket:

```python
import asyncio
import websockets
import json
from datetime import datetime, timedelta

class TaskClient:
    def __init__(self, uri="ws://localhost:8000/ws"):
        self.uri = uri

    async def send_query(self, query: str):
        async with websockets.connect(self.uri) as websocket:
            print(f"Sending: {query}")
            await websocket.send(query)
            response = await websocket.recv()
            return json.loads(response)

    async def demonstrate_operations(self):
        # 1. Create a new project
        await self.send_query("Create a project called 'Website Redesign' with description 'Updating company website'")
        
        # 2. Create tasks with different priorities and due dates
        await self.send_query("Create a task 'Design mockups' with high priority for project 'Website Redesign' due next Friday")
        await self.send_query("Add a task 'Update content' with medium priority due tomorrow")
        
        # 3. Add tags to tasks
        await self.send_query("Add tag 'design' to task 'Design mockups'")
        await self.send_query("Add tag 'urgent' to task 'Design mockups'")
        
        # 4. Query tasks in different ways
        await self.send_query("Show all high priority tasks")
        await self.send_query("Show tasks due this week")
        await self.send_query("Show tasks with tag 'design'")
        await self.send_query("List all tasks in project 'Website Redesign'")
        
        # 5. Update task status
        await self.send_query("Mark task 'Update content' as in progress")
        
        # 6. Assign tasks
        await self.send_query("Assign task 'Design mockups' to user 'testuser'")
        
        # 7. Change task priority
        await self.send_query("Change priority of task 'Update content' to high")
        
        # 8. Delete operations
        await self.send_query("Remove tag 'urgent' from task 'Design mockups'")
        await self.send_query("Delete task 'Update content'")

async def main():
    client = TaskClient()
    await client.demonstrate_operations()

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript/Node.js WebSocket Client

Here's how to interact with the system using JavaScript:

```javascript
const WebSocket = require('ws');

class TaskClient {
    constructor(uri = 'ws://localhost:8000/ws') {
        this.uri = uri;
    }

    async sendQuery(query) {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket(this.uri);

            ws.on('open', () => {
                console.log(`Sending: ${query}`);
                ws.send(query);
            });

            ws.on('message', (data) => {
                resolve(JSON.parse(data));
                ws.close();
            });

            ws.on('error', (error) => {
                reject(error);
            });
        });
    }

    async demonstrateOperations() {
        try {
            // Create project and tasks
            await this.sendQuery("Create project 'Mobile App' with description 'New mobile application development'");
            
            // Create tasks with different attributes
            const tasks = [
                "Create task 'UI Design' with high priority for project 'Mobile App' due next week",
                "Add task 'API Integration' with medium priority due in 3 days",
                "Create task 'Testing' with low priority"
            ];

            for (const task of tasks) {
                const response = await this.sendQuery(task);
                console.log('Task creation response:', response);
            }

            // Query tasks
            const queries = [
                "Show all tasks in project 'Mobile App'",
                "Show high priority tasks",
                "Show tasks due this week"
            ];

            for (const query of queries) {
                const response = await this.sendQuery(query);
                console.log(`Query "${query}" response:`, response);
            }

        } catch (error) {
            console.error('Error:', error);
        }
    }
}

// Usage
const client = new TaskClient();
client.demonstrateOperations();
```

### Browser JavaScript WebSocket Client

Here's how to interact with the system from a web browser:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Task Management Client</title>
</head>
<body>
    <div>
        <input type="text" id="query" placeholder="Enter your task query">
        <button onclick="sendQuery()">Send</button>
    </div>
    <div id="response"></div>

    <script>
        const ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onopen = () => {
            console.log('Connected to task management server');
        };
        
        ws.onmessage = (event) => {
            const response = JSON.parse(event.data);
            document.getElementById('response').innerHTML = 
                `<pre>${JSON.stringify(response, null, 2)}</pre>`;
        };
        
        function sendQuery() {
            const query = document.getElementById('query').value;
            ws.send(query);
        }

        // Example queries you can try:
        const exampleQueries = [
            "Create task 'Review PR' with high priority",
            "Show all my tasks",
            "Mark task 'Review PR' as completed",
            "Show high priority tasks",
            "Delete task 'Review PR'"
        ];
    </script>
</body>
</html>
```

### Common Operations Examples

Here are some common operations and their natural language queries:

1. **Task Creation with Full Details**
```python
queries = [
    "Create task 'Quarterly Report' with high priority due next Friday for project 'Finance' and assign to user 'testuser'",
    "Add task 'Client Meeting' due tomorrow at 2pm with medium priority and tag 'client-facing'"
]
```

2. **Complex Task Queries**
```python
queries = [
    "Show all high priority tasks due this week assigned to testuser",
    "Find tasks with tag 'urgent' or 'important' in project 'Website Redesign'",
    "List overdue tasks with status 'in_progress'"
]
```

3. **Batch Operations**
```python
queries = [
    "Mark all tasks in project 'Old Website' as completed",
    "Delete all completed tasks older than 30 days",
    "Assign all unassigned high priority tasks to testuser"
]
```

4. **Project Management**
```python
queries = [
    "Create project 'Q4 Planning' with description 'Fourth quarter planning and execution'",
    "Move all tasks with tag 'frontend' to project 'UI Redesign'",
    "Show project 'Marketing Campaign' progress"
]
```

### Response Format

The server responds with JSON in the following format:

```json
{
    "success": true,
    "response": "Natural language response describing the action taken",
    "data": {
        // Operation-specific data
        // For example, for a task creation:
        "task_id": 1,
        "title": "Example Task",
        "priority": "high",
        "status": "pending",
        "due_date": "2024-01-01T00:00:00",
        "assigned_to": 1
    }
}
```