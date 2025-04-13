"""Report schemas for API requests and responses."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ReportBase(BaseModel):
    """Base Report schema."""
    title: str
    description: Optional[str] = None
    video_id: int
    team_name: Optional[str] = None
    opponent_name: Optional[str] = None
    game_date: Optional[datetime] = None


class ReportCreate(ReportBase):
    """Report creation schema."""
    user_id: int
    video_title: Optional[str] = None


class ReportUpdate(BaseModel):
    """Report update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    team_name: Optional[str] = None
    opponent_name: Optional[str] = None
    game_date: Optional[datetime] = None
    status: Optional[str] = None
    file_path: Optional[str] = None
    analysis_results: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None


class ReportInDBBase(ReportBase):
    """Base Report in DB schema."""
    id: int
    user_id: int
    video_title: Optional[str] = None
    status: str
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Report(ReportInDBBase):
    """Report schema for API responses."""
    analysis_results: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None


class ReportInDB(ReportInDBBase):
    """Report schema for database."""
    analysis_results: Optional[Dict[str, Any]] = None


class PlayerAnalysis(BaseModel):
    """Player analysis schema."""
    player_id: Optional[int] = None
    jersey_number: Optional[str] = None
    name: Optional[str] = None
    position: Optional[str] = None
    height: Optional[str] = None
    physical_attributes: Dict[str, Any] = Field(default_factory=dict)
    offensive_role: Dict[str, Any] = Field(default_factory=dict)
    defensive_role: Dict[str, Any] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    strategy_notes: Optional[str] = None


class TeamAnalysis(BaseModel):
    """Team analysis schema."""
    team_name: str
    players: List[PlayerAnalysis] = Field(default_factory=list)
    offensive_style: Dict[str, Any] = Field(default_factory=dict)
    defensive_style: Dict[str, Any] = Field(default_factory=dict)
    team_strengths: List[str] = Field(default_factory=list)
    team_weaknesses: List[str] = Field(default_factory=list)
    recommended_strategy: Optional[str] = None
