"""Global error handling middleware."""
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.responses import ResponseModel
from app.core.logging import logger


def add_error_handlers(app: FastAPI) -> None:
    """Add error handlers to the application."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseModel.error(
                message=exc.detail,
                status_code=exc.status_code,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors."""
        # Extract useful information from the validation error
        error_details: List[dict] = []
        for error in exc.errors():
            error_details.append({
                "loc": " -> ".join([str(loc) for loc in error["loc"]]),
                "msg": error["msg"],
                "type": error["type"]
            })

        # Determine user-friendly message
        user_message = "Invalid request format"

        # Check for common validation problems and provide more specific messages
        if error_details:
            first_error = error_details[0]
            if "missing" in first_error["msg"].lower():
                if "body" in first_error["loc"]:
                    user_message = "Missing request body"
                else:
                    field = first_error["loc"].split(" -> ")[-1]
                    user_message = f"Missing required field: {field}"
            elif "not valid" in first_error["msg"].lower() and "email" in first_error["loc"]:
                user_message = "Invalid email format"
            elif "field required" in first_error["msg"].lower():
                field = first_error["loc"].split(" -> ")[-1]
                user_message = f"Required field missing: {field}"
            elif "password" in first_error["loc"] and "string" in first_error["msg"].lower():
                user_message = "Password must be a string"

        logger.warning(f"Validation error: {user_message}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ResponseModel.error(
                message=user_message,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_detail=error_details,
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        """Handle all other exceptions."""
        # Log the error
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ResponseModel.error(
                message="An unexpected error occurred. Please try again later.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_detail=str(exc) if app.debug else None,
            ),
        )