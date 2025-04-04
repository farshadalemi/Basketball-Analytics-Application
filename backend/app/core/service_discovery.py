"""Service discovery module for microservice integration."""
import os
from typing import Dict, List, Optional
import requests
from app.core.config import settings
from app.core.logging import logger


class ServiceRegistry:
    """
    Service registry for microservice discovery.
    
    This class provides methods to register and discover microservices.
    It can be extended to use external service discovery tools like Consul or Eureka.
    """
    
    def __init__(self):
        """Initialize the service registry."""
        self.services: Dict[str, Dict[str, str]] = {}
        self.service_name = os.getenv("SERVICE_NAME", "video-service")
        self.service_url = os.getenv("SERVICE_URL", "http://localhost:8000")
        
        # Register this service
        self.register_service(self.service_name, self.service_url)
    
    def register_service(self, name: str, url: str) -> None:
        """
        Register a service.
        
        Args:
            name: The name of the service
            url: The URL of the service
        """
        self.services[name] = {"url": url}
        logger.info(f"Registered service: {name} at {url}")
    
    def get_service(self, name: str) -> Optional[Dict[str, str]]:
        """
        Get a service by name.
        
        Args:
            name: The name of the service
            
        Returns:
            The service information or None if not found
        """
        return self.services.get(name)
    
    def get_service_url(self, name: str) -> Optional[str]:
        """
        Get a service URL by name.
        
        Args:
            name: The name of the service
            
        Returns:
            The service URL or None if not found
        """
        service = self.get_service(name)
        return service["url"] if service else None
    
    def list_services(self) -> List[Dict[str, str]]:
        """
        List all registered services.
        
        Returns:
            A list of service information
        """
        return [{"name": name, **info} for name, info in self.services.items()]
    
    def call_service(self, name: str, endpoint: str, method: str = "GET", **kwargs) -> Optional[Dict]:
        """
        Call a service endpoint.
        
        Args:
            name: The name of the service
            endpoint: The endpoint to call
            method: The HTTP method to use
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            The response from the service or None if the service is not found
        """
        service_url = self.get_service_url(name)
        if not service_url:
            logger.error(f"Service not found: {name}")
            return None
        
        url = f"{service_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling service {name}: {str(e)}")
            return None


# Create a singleton instance
service_registry = ServiceRegistry()
