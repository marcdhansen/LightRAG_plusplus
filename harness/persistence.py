from langgraph.checkpoint.sqlite import SqliteSaver


def get_sqlite_checkpointer(db_path: str = "harness_state.db"):
    """
    Returns a SqliteSaver checkpointer for persistent state storage.
    """
    return SqliteSaver.from_conn_string(f"file:{db_path}?check_same_thread=False")
