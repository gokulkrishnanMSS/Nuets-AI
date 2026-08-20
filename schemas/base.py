from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Shared configuration for every request and response schema.

    Every schema in this package inherits from this class so validation
    behaviour stays consistent across the API.
    """

    model_config = ConfigDict(
        # Trim accidental padding on incoming text fields, e.g. a food
        # description pasted with a trailing newline.
        str_strip_whitespace=True,
        populate_by_name=True
    )
