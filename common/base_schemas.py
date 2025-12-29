# from typing import List, Optional, Type, TypeVar, Union
# from uuid import UUID, uuid4

# from ninja import Schema
# from pydantic import create_model


# class APIResponseBase(Schema):
#     error: Optional[dict] = None
#     trace_id: UUID

#     @classmethod
#     def success(cls, data: Schema):
#         """Create a successful response with data and trace_id"""
#         return cls(error=None, trace_id=uuid4(), **{"data": data})

#     @classmethod
#     def failure(cls, error_message: str):
#         """Create a failure response with an error message"""
#         return cls(error={"message": error_message}, trace_id=uuid4())


# T = TypeVar("T", bound=Schema)


# def create_api_response_schema(data_schema: Type[T]) -> Type[Schema]:
#     """Dynamically generate an API response schema for a given data type"""

#     class APIResponse(APIResponseBase):
#         data: Optional[Union[data_schema, List[data_schema]]] = None  # Support both single and list

#     return APIResponse


# # def create_api_response_schema(data_schema: Type[T]) -> Type[Schema]:
# #     """Dynamically generate an API response schema for a given data type"""

# #     return create_model(
# #         f"APIResponse[{data_schema.__name__}]",  # Unique model name
# #         data=(Optional[Union[data_schema, List[data_schema]]], None),  # Support single and list
# #         error=(Optional[dict], None),
# #         trace_id=(str, ...),  # Required field
# #     )


from typing import List, Optional, Type, TypeVar, Union

from ninja import Schema
from pydantic import create_model

T = TypeVar("T", bound=Schema)


class APIResponseBase(Schema):
    trace_id: str
    error: Optional[dict] = None


def create_api_response_schema(data_schema: Type[T]):
    """
    Dynamically create proper response schema that swagger can introspect.
    """
    fields = {
        "trace_id": (str, ...),
        "error": (Optional[dict], None),
        "data": (Optional[Union[data_schema, List[data_schema]]], None),
    }

    model = create_model(
        f"{data_schema.__name__}Response",  # 👈 Proper named schema for Swagger
        __base__=APIResponseBase,
        **fields,
    )
    return model


class MessageSchema(Schema):
    message: str
