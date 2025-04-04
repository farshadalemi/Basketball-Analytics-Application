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
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_detail: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Create an error response.
        
        Args:
            message: An error message
            status_code: HTTP status code
            error_detail: Additional error details
            
        Returns:
            A dictionary with the error data
        """
        response = {
            "status": "error",
            "message": message,
            "code": status_code,
        }
        
        if error_detail:
            response["error_detail"] = error_detail
            
        return response


class APIResponse:
    """API response utilities."""
    
    @staticmethod
    def success_response(
        data: Optional[Any] = None,
        message: str = "Operation successful",
        status_code: int = status.HTTP_200_OK,
    ) -> JSONResponse:
        """
        Create a success JSON response.
        
        Args:
            data: The data to return
            message: A success message
            status_code: HTTP status code
            
        Returns:
            A JSONResponse with the response data
        """
        return JSONResponse(
            status_code=status_code,
            content=ResponseModel.success(
                data=data,
                message=message,
                status_code=status_code,
            ),
        )
    
    @staticmethod
    def error_response(
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_detail: Optional[Any] = None,
    ) -> JSONResponse:
        """
        Create an error JSON response.
        
        Args:
            message: An error message
            status_code: HTTP status code
            error_detail: Additional error details
            
        Returns:
            A JSONResponse with the error data
        """
        return JSONResponse(
            status_code=status_code,
            content=ResponseModel.error(
                message=message,
                status_code=status_code,
                error_detail=error_detail,
            ),
        )
