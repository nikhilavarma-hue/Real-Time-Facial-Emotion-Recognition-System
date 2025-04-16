"""
Database connection and initialization module.
"""
import sqlite3
import os
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    """
    Get a database connection.
    
    Returns:
        sqlite3.Connection: Database connection with row factory set to sqlite3.Row
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_URI'].replace('sqlite:///', ''),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    
    return g.db

def init_db():
    """Initialize the database by executing schema.sql."""
    db = get_db()
    
    # Get the path to the schema file
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    # Execute the schema file
    with open(schema_path, 'r') as f:
        db.executescript(f.read())
    
    # Commit the changes
    db.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def register_db_commands(app):
    """Register database commands with the Flask application."""
    app.cli.add_command(init_db_command)