"""Event system for microservice communication."""
import asyncio
import json
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from app.core.logging import logger


class EventType(str, Enum):
    """Event types for the application."""
    # Video events
    VIDEO_CREATED = "video.created"
    VIDEO_UPDATED = "video.updated"
    VIDEO_DELETED = "video.deleted"
    VIDEO_PROCESSED = "video.processed"
    
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class EventBus:
    """
    Event bus for publishing and subscribing to events.
    
    This is a simple in-memory event bus that can be extended to use
    external message brokers like RabbitMQ or Kafka.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self.subscribers: Dict[EventType, Set[Callable]] = {}
        
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_type: The type of event to subscribe to
            callback: The callback function to call when the event is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = set()
        self.subscribers[event_type].add(callback)
        logger.info(f"Subscribed to event: {event_type}")
        
    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            logger.info(f"Unsubscribed from event: {event_type}")
            
    async def publish(self, event_type: EventType, data: Any = None) -> None:
        """
        Publish an event.
        
        Args:
            event_type: The type of event to publish
            data: The data to publish with the event
        """
        logger.info(f"Publishing event: {event_type}")
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, data)
                    else:
                        callback(event_type, data)
                except Exception as e:
                    logger.error(f"Error in event callback: {str(e)}")


# Create a singleton instance
event_bus = EventBus()
