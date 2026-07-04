def format_doc(doc: dict):
    if not doc:
        return None
    result = dict(doc)
    result.pop("_id", None)
    return result
