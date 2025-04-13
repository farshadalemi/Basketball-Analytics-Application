"""Standardized API response formats."""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar('T')


class ResponseModel(Generic[T]):
    """Standard response model for API endpoints."""

    @staticmethod
    def success(
        data: Optional[T] = None,
        message: str = "Operation successful",
        status_code: int = status.HTTP_200_OK,
    ) -> Dict[str, Any]:
        """
        Create a success response.
        
        Args:
            data: The data to return
            message: A success message
            status_code: HTTP status code
            
        Returns:
            A dictionary with the response data
        """
        return {
            "status": "success",
            "message": message,
            "data": data,
            "code": status_code,
        }

    @staticmethod
    def error(
        message: str = "An error occurred",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create an error response.
        
        Args:
            message: An error message
            status_code: HTTP status code
            errors: A list of error details
            
        Returns:
            A dictionary with the error data
        """
        return {
            "status": "error",
            "message": message,
            "errors": errors or [],
            "code": status_code,
        }
