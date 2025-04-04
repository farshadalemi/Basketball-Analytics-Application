"""Base service interface for microservice integration."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')


class BaseServiceInterface(Generic[T], ABC):
    """
    Base service interface for microservice integration.
    
    This interface defines the standard methods that all services should implement
    to ensure consistent behavior across microservices.
    """
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """
        Get a single resource by ID.
        
        Args:
            id: The ID of the resource
            
        Returns:
            The resource or None if not found
        """
        pass
    
    @abstractmethod
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get multiple resources.
        
        Args:
            skip: Number of resources to skip
            limit: Maximum number of resources to return
            
        Returns:
            A list of resources
        """
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new resource.
        
        Args:
            data: The data to create the resource with
            
        Returns:
            The created resource
        """
        pass
    
    @abstractmethod
    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Update a resource.
        
        Args:
            id: The ID of the resource to update
            data: The data to update the resource with
            
        Returns:
            The updated resource or None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """
        Delete a resource.
        
        Args:
            id: The ID of the resource to delete
            
        Returns:
            True if the resource was deleted, False otherwise
        """
        pass
