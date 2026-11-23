import os

from flask_migrate import Migrate

from app import db
from app import create_app

app = create_app(os.getenv("FLASK_CONFIG") or "default")
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    """
    Make application objects available in the Python Flask Interactive Shell
    """
    return dict(db=db)


@app.cli.command("init-db")
def init_db():
    """Create missing tables without dropping existing data."""
    import app.models
    db.create_all()
    print("Database tables are ready.")


if __name__ == "__main__":
    app.run()
