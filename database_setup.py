"""
Author: Imran Mughal
Email: imran@mughal.com
Date: December 19, 2024
"""

import sqlite3
import os
from datetime import datetime

def create_database():
    # Remove existing database if it exists
    if os.path.exists('tasks.db'):
        os.remove('tasks.db')

    # Connect to database (this will create it if it doesn't exist)
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute('PRAGMA foreign_keys = ON')

    # Create users table
    cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create projects table
    cursor.execute('''
    CREATE TABLE projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create tasks table
    cursor.execute('''
    CREATE TABLE tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'completed')) DEFAULT 'pending',
        priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
        due_date TIMESTAMP,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        project_id INTEGER,
        assigned_to INTEGER,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_to) REFERENCES users(user_id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
    )
    ''')

    # Create tags table
    cursor.execute('''
    CREATE TABLE tags (
        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE,
        UNIQUE(name, created_by)
    )
    ''')

    # Create task_tags junction table
    cursor.execute('''
    CREATE TABLE task_tags (
        task_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (task_id, tag_id),
        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
    )
    ''')

    # Create indexes for frequently queried columns
    cursor.execute('CREATE INDEX idx_tasks_status ON tasks(status)')
    cursor.execute('CREATE INDEX idx_tasks_priority ON tasks(priority)')
    cursor.execute('CREATE INDEX idx_tasks_due_date ON tasks(due_date)')
    cursor.execute('CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to)')
    cursor.execute('CREATE INDEX idx_tasks_project_id ON tasks(project_id)')

    # Commit changes and close connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
    print("Database 'tasks.db' has been created successfully with all tables and constraints.") 