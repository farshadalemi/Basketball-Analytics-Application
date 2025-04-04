"""Analytics service interface for microservice integration."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.interfaces.base_service_interface import BaseServiceInterface


class AnalyticsServiceInterface(BaseServiceInterface[Dict[str, Any]], ABC):
    """
    Analytics service interface for microservice integration.
    
    This interface defines the methods that an analytics service should implement.
    It can be implemented by a local service or a remote microservice.
    """
    
    @abstractmethod
    async def track_event(self, event_name: str, properties: Dict[str, Any]) -> bool:
        """
        Track an event.
        
        Args:
            event_name: The name of the event
            properties: The properties of the event
            
        Returns:
            True if the event was tracked successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def track_video_view(self, video_id: int, user_id: Optional[int] = None) -> bool:
        """
        Track a video view.
        
        Args:
            video_id: The ID of the video
            user_id: The ID of the user who viewed the video, if available
            
        Returns:
            True if the view was tracked successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_video_views(self, video_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> int:
        """
        Get the number of views for a video.
        
        Args:
            video_id: The ID of the video
            start_date: The start date for the view count, if provided
            end_date: The end date for the view count, if provided
            
        Returns:
            The number of views for the video
        """
        pass
    
    @abstractmethod
    async def get_popular_videos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most popular videos.
        
        Args:
            limit: The maximum number of videos to return
            
        Returns:
            A list of popular videos with their view counts
        """
        pass
    
    @abstractmethod
    async def get_user_activity(self, user_id: int) -> Dict[str, Any]:
        """
        Get activity data for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Activity data for the user
        """
        pass
