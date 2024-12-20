from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, CheckConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# Junction table for task-tag relationship
task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.task_id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('tags.tag_id', ondelete='CASCADE'))
)

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    created_tasks = relationship('Task', back_populates='creator', foreign_keys='Task.created_by')
    assigned_tasks = relationship('Task', back_populates='assignee', foreign_keys='Task.assigned_to')
    created_tags = relationship('Tag', back_populates='creator')

class Project(Base):
    __tablename__ = 'projects'
    
    project_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship('Task', back_populates='project')

class Task(Base):
    __tablename__ = 'tasks'
    
    task_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False, default='pending')
    priority = Column(String, nullable=False, default='medium')
    due_date = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    project_id = Column(Integer, ForeignKey('projects.project_id', ondelete='SET NULL'))
    assigned_to = Column(Integer, ForeignKey('users.user_id', ondelete='SET NULL'))
    created_by = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(status.in_(['pending', 'in_progress', 'completed'])),
        CheckConstraint(priority.in_(['low', 'medium', 'high'])),
    )
    
    # Relationships
    project = relationship('Project', back_populates='tasks')
    creator = relationship('User', back_populates='created_tasks', foreign_keys=[created_by])
    assignee = relationship('User', back_populates='assigned_tasks', foreign_keys=[assigned_to])
    tags = relationship('Tag', secondary=task_tags, back_populates='tasks')

class Tag(Base):
    __tablename__ = 'tags'
    
    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    creator = relationship('User', back_populates='created_tags')
    tasks = relationship('Task', secondary=task_tags, back_populates='tags') 