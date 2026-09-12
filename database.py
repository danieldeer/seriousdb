# Database work

import pickle

db_file = ".sdb"


# Use it for getting db with Depends from fastapi
def get_db():
    """db session for data viewing"""
    with open(db_file, "rb") as f:
        yield pickle.load(f)


def edit_db():
    """db session to edit or add data"""
    with open(db_file, "rb") as f:
        db = pickle.load(f)

    yield db

    with open(db_file, "wb") as f:
        pickle.dump(db, f)
