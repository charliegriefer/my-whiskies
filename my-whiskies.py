from datetime import datetime

from app import create_app, db
from app.models import User

application = create_app()


@application.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User}


@application.context_processor
def inject_today_date():
    return {"current_date": datetime.today()}
