import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


def get_sqlite_checkpointer(db_path: str = "harness_state.db"):
    """
    Returns a SqliteSaver checkpointer for persistent state storage.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)
