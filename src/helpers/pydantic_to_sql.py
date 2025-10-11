from typing import get_origin, get_args, List, Dict, Union
from pydantic import BaseModel

_SIMPLE_TYPE_MAP = {
    int: "INTEGER",
    float: "REAL",
    bool: "INTEGER",
    str: "TEXT",
}

def _sqlite_type_from_annotation(annotation) -> str:
    """Return a SQLite column type string for a given type annotation."""
    origin = get_origin(annotation)

    # Optional[T] or Union[T, None] -> unwrap
    if origin is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]  # noqa: E721
        if len(args) == 1:
            return _sqlite_type_from_annotation(args[0])
        # multiple types: fall back to TEXT (JSON)
        return "TEXT"

    # Lists / Dicts / other generics -> TEXT (store as JSON)
    if origin in (list, List, dict, Dict):
        return "TEXT"

    # If it's a pydantic model class (subclass of BaseModel), we will flatten it
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        # signal to caller it's nested model (handled separately)
        return "NESTED_MODEL"

    # Simple builtin types
    if annotation in _SIMPLE_TYPE_MAP:
        return _SIMPLE_TYPE_MAP[annotation]

    # Fallback: treat as TEXT (JSON)
    return "TEXT"


def _collect_fields_from_model(model_cls: type[BaseModel], prefix: str = "") -> List[tuple]:
    """
    Return list of (column_name, sqlite_type, not_null_flag) tuples for fields in model_cls.
    Nested BaseModel fields will be flattened with prefix.
    """
    fields = []

    # Prefer pydantic .__fields__ if present
    pyd_fields = getattr(model_cls, "__fields__", None)
    if pyd_fields is not None:
        iter_fields = pyd_fields.items()
    else:
        # fallback to annotations
        iter_fields = getattr(model_cls, "__annotations__", {}).items()

    for name, field_info in iter_fields:
        # Try to get annotation type (works from __annotations__)
        annotation = None
        required = True
        if hasattr(field_info, "outer_type_"):
            annotation = field_info.outer_type_
            # required property might be on field_info.required (v1) or not
            required = getattr(field_info, "required", True)
        else:
            # fallback: annotation from annotations dict
            ann = getattr(model_cls, "__annotations__", {}).get(name)
            annotation = ann
            # assume required unless Optional[...] in annotation
            origin = get_origin(annotation)
            if origin is Union and type(None) in get_args(annotation):
                required = False

        col_type = _sqlite_type_from_annotation(annotation)

        if col_type == "NESTED_MODEL":
            # flatten nested BaseModel fields
            nested_cls = get_args(annotation)[0] if get_origin(annotation) is Union else annotation
            nested_prefix = f"{prefix}{name}_"
            nested_fields = _collect_fields_from_model(nested_cls, prefix=nested_prefix)
            fields.extend(nested_fields)
        else:
            col_name = f"{prefix}{name}"
            # decide NOT NULL: if required True -> NOT NULL, else allow NULL
            not_null = required
            fields.append((col_name, col_type, not_null))

    return fields


def pydantic_model_to_create_table_sql(
    model_cls: type[BaseModel],
    table_name: str,
    extra_columns: List[tuple] | None = None,
    add_id_pk: bool = True,
    add_timestamp: bool = True,
) -> str:
    """
    Generate a CREATE TABLE string for a pydantic model class.

    extra_columns: list of (col_name, sql_type, not_null_flag), e.g. [("func_name", "TEXT", True)]
    """
    cols = []

    if add_id_pk:
        cols.append("id INTEGER PRIMARY KEY AUTOINCREMENT")

    # collect model fields (flattening nested models)
    model_fields = _collect_fields_from_model(model_cls)
    for name, sql_type, not_null in model_fields:
        if not_null:
            cols.append(f"{name} {sql_type} NOT NULL")
        else:
            cols.append(f"{name} {sql_type}")

    # extra columns
    if extra_columns:
        for name, sql_type, not_null in extra_columns:
            if not_null:
                cols.append(f"{name} {sql_type} NOT NULL")
            else:
                cols.append(f"{name} {sql_type}")

    if add_timestamp:
        cols.append("timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")

    cols_sql = ",\n    ".join(cols)
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {cols_sql}\n)"
    return create_sql
