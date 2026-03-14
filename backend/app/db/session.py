from threading import Lock

from sqlmodel import Session, SQLModel, create_engine, select

from app.config import settings
from app.core.security import hash_text
from app.db.models import Organization, User, UserCredential, Workspace, WorkspaceMembership


engine = create_engine(settings.database_url, echo=False)
_init_lock = Lock()
_db_initialized = False


def init_db() -> None:
    global _db_initialized

    if _db_initialized:
        return

    with _init_lock:
        if _db_initialized:
            return
        SQLModel.metadata.create_all(engine)
        seed_demo_data()
        _db_initialized = True


def get_session() -> Session:
    return Session(engine)


def seed_demo_data() -> None:
    with Session(engine) as session:
        organization = session.get(Organization, "demo-org")
        if organization is None:
            session.add(Organization(id="demo-org", name="Demo Organization"))

        workspace = session.get(Workspace, "demo-workspace")
        if workspace is None:
            session.add(Workspace(id="demo-workspace", organization_id="demo-org", name="Demo Workspace"))

        user = session.get(User, "demo-user")
        if user is None:
            session.add(User(id="demo-user", email="demo@company.com", full_name="Demo User"))

        membership_statement = select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == "demo-user",
            WorkspaceMembership.workspace_id == "demo-workspace",
        )
        membership = session.exec(membership_statement).first()
        if membership is None:
            session.add(
                WorkspaceMembership(
                    user_id="demo-user",
                    workspace_id="demo-workspace",
                    role="manager",
                )
            )

        credential = session.get(UserCredential, "demo-user")
        if credential is None:
            session.add(UserCredential(user_id="demo-user", password_hash=hash_text("demo-pass")))

        session.commit()
