# File that stores functions that are used repeatedly a lot


def get_key_value(key, db):
    """Function that gets value from database key"""

    value = db.get(key)

    if value is None:
        return None

    return {key: value}


def add_key_value(db, data: dict):
    """Function adds keys and values using dictionary
    and more efficient to edit db fast instead of manually
    repeating same function to add"""
    db.update(data)
    return data
