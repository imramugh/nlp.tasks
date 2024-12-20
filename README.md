# Natural Language Task Management System

A modern task management system that allows users to interact with tasks using natural language through a command-line interface. Built with SQLAlchemy, SQLite, and OpenAI's GPT-4 for natural language processing.

## Features

### Core Features
- ✅ Natural language interface for task management
- ✅ Task organization by projects
- ✅ Priority and status tracking
- ✅ Due date management
- ✅ User assignment capabilities
- ✅ GPT-4 powered task generation and import
- ✅ Bulk task operations
- ✅ Schema inspection and management

### Task Management
- Create and manage tasks with natural language
- Set task priorities (high, medium, low)
- Track task status (pending, in_progress, completed)
- Assign tasks to users
- Associate tasks with projects
- Set and manage due dates
- Bulk update task properties
- Import generated tasks to projects

### Project Management
- Create and manage projects
- List and search projects
- Delete projects (single or bulk)
- Associate tasks with projects
- View project-specific task lists

### User Management
- Create new users
- Search and list users
- Assign users to tasks
- Basic user authentication

### Natural Language Processing
- Generate structured tasks from natural language descriptions
- Parse and interpret natural language commands
- GPT-4 integration for intelligent task generation
- Structured response handling

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

## Usage

### Starting the Application

1. Start the server:
```bash
./server.sh start
```

2. In a new terminal, start the client:
```bash
./client.sh
```

### Natural Language Commands

#### Task Generation and Management

1. **Generating Tasks**
```
what are the top 10 tasks for a middle aged man to get fit?
how to plan a wedding?
what are the steps to start a business?
```

2. **Importing Generated Tasks**
```
add these tasks
import tasks to project "Fitness Goals"
save these tasks to project "Wedding Planning"
```

3. **Creating Tasks**
```
create task "Review documentation" with high priority
add task "Team meeting" due tomorrow
create task "Update website" for project "Marketing"
```

4. **Updating Tasks**
```
set all tasks to project 3
assign all tasks to user 2
mark task 1 as completed
change priority of task 2 to high
```

5. **Viewing Tasks**
```
show tasks
show all tasks in project "Marketing"
show high priority tasks
show tasks due this week
```

6. **Bulk Operations**
```
set all tasks to project 3
assign all tasks to user 2
delete all tasks
mark all tasks as completed
```

#### Project Management

1. **Creating Projects**
```
create project "Website Redesign"
add project "Marketing Campaign"
```

2. **Viewing Projects**
```
show projects
list all projects
```

3. **Deleting Projects**
```
delete project 1
delete all projects
```

#### User Management

1. **Creating Users**
```
add user john with email john@example.com
create user sarah with email sarah@example.com
```

2. **Viewing Users**
```
show users
list all users
```

3. **Task Assignment**
```
assign task 1 to john
set all tasks to user 2
```

#### System Commands

1. **Schema Management**
```
show schema
show tables
```

2. **System Control**
```
exit
help
```

## Database Schema

The system uses SQLite with the following tables:

### users
- user_id (PRIMARY KEY)
- username
- email
- created_at

### projects
- project_id (PRIMARY KEY)
- name
- description
- created_at

### tasks
- task_id (PRIMARY KEY)
- title
- description
- status
- priority
- due_date
- created_at
- project_id (FOREIGN KEY)
- assigned_to (FOREIGN KEY)
- created_by (FOREIGN KEY)

### tags
- tag_id (PRIMARY KEY)
- name
- created_by (FOREIGN KEY)

### task_tags
- task_id (FOREIGN KEY)
- tag_id (FOREIGN KEY)

## Error Handling

The system provides clear error messages for:
- Invalid commands or queries
- Missing required parameters
- Database operation failures
- Invalid data formats
- API communication errors
- JSON parsing errors

## Future Enhancements

1. Task Dependencies
   - Dependency tracking
   - Circular dependency prevention

2. Recurring Tasks
   - Recurrence patterns
   - Automatic task generation

3. Task Comments
   - Comment threading
   - User mentions

4. Task Attachments
   - File upload support
   - Attachment management

5. Team Management
   - Team creation
   - Role management

6. Audit Logging
   - Activity tracking
   - Change history

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.