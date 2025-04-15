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


class DefensiveAnalysis(BaseModel):
    """Defensive analysis schema."""
    # Defense type
    defense_type: str = Field(description="Type of defense: Man-to-Man, Zone, Combination, etc.")
    defense_subtype: Optional[str] = Field(None, description="Subtype of defense: 2-3 Zone, 1-3-1 Zone, etc.")

    # Defense characteristics
    pressure_level: str = Field(description="Pressure level: High, Medium, Low")
    pick_up_point: str = Field(description="Pick up point: Full Court, 3/4 Court, Half Court, 3pt Line")

    # Defensive tendencies
    deny_first_pass: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    deny_ball_reversal: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    allow_dribble_penetration: str = Field(description="Frequency: Frequently, Occasionally, Seldom")

    # Transition defense
    transition_defense_speed: str = Field(description="Speed: Quick, Medium, Slow")
    vulnerable_to_fast_break: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    vulnerable_to_long_passes: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    pressure_rebounder: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    pressure_outlet_pass: str = Field(description="Frequency: Frequently, Occasionally, Seldom")

    # Post defense
    post_defense_strength: str = Field(description="Strength: Strong, Medium, Soft, Weak")
    post_defense_deployment: str = Field(description="Deployment: Front, Behind, 3/4, Push Out, Trap")
    allow_post_feeds: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    post_feed_reaction: str = Field(description="Reaction: Collapse, Play 1/2 way Off, Trap, None")
    post_lob_defense: str = Field(description="Defense: Collapse, Trap, None")

    # Screen defense
    on_ball_screen_strength: str = Field(description="Strength: Strong, Medium, Soft, Weak")
    on_ball_screen_primary: str = Field(description="Primary: Show & Recover, Switch, Trap, Fight Over, Go Under")
    off_ball_screen_strength: str = Field(description="Strength: Strong, Medium, Soft, Weak")
    off_ball_screen_primary: str = Field(description="Primary: Chase Out, Show & Recover, Switch, Go Under")

    # Help defense
    helpside_defense: str = Field(description="Strength: Strong, Medium, Soft, Weak")
    deny_lane_cuts: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    trap_dribble_penetration: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    closeout_quality: str = Field(description="Quality: Quick (on Balance), Slow, Rushed (off balance)")
    box_out_frequency: str = Field(description="Frequency: Frequently, Occasionally, Seldom")

    # Zone defense (if applicable)
    zone_activity: Optional[str] = Field(None, description="Activity: Active, Medium, Soft, Weak")
    zone_ball_pressure: Optional[str] = Field(None, description="Frequency: Frequently, Occasionally, Seldom")
    zone_post_fronting: Optional[str] = Field(None, description="Frequency: Frequently, Occasionally, Seldom")
    zone_trapping: Optional[str] = Field(None, description="Frequency: Frequently, Occasionally, Seldom")
    zone_shifts: Optional[str] = Field(None, description="Shifts: Quick, Medium, Slow, Rushed")

    # Special situations
    extend_defense_frequency: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    primary_press: Optional[str] = Field(None, description="Primary press type")
    secondary_press: Optional[str] = Field(None, description="Secondary press type")
    deny_inbounds: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    trap_first_pass: str = Field(description="Frequency: Frequently, Occasionally, Seldom")
    baseline_out_defense: str = Field(description="Strength: Strong, Medium, Soft, Weak")
    sideline_out_defense: str = Field(description="Strength: Strong, Medium, Soft, Weak")

    # Key defensive personnel
    best_on_ball_defenders: List[str] = Field(default_factory=list)
    weak_on_ball_defenders: List[str] = Field(default_factory=list)
    best_post_defenders: List[str] = Field(default_factory=list)
    weak_post_defenders: List[str] = Field(default_factory=list)
    best_defensive_rebounders: List[str] = Field(default_factory=list)
    best_shot_blockers: List[str] = Field(default_factory=list)
    weakside_ball_watchers: List[str] = Field(default_factory=list)
    slow_transition_defenders: List[str] = Field(default_factory=list)

    # Analysis notes
    vulnerable_screen_types: Optional[str] = Field(None)
    last_shot_defense: Optional[str] = Field(None)
    combination_defenses: Optional[Dict[str, Any]] = Field(default_factory=dict)
    notes: Optional[str] = Field(None)


class TeamAnalysis(BaseModel):
    """Team analysis schema."""
    team_name: str
    players: List[PlayerAnalysis] = Field(default_factory=list)
    offensive_style: Dict[str, Any] = Field(default_factory=dict)
    defensive_style: Dict[str, Any] = Field(default_factory=dict)
    defensive_analysis: Optional[DefensiveAnalysis] = Field(None)
    team_strengths: List[str] = Field(default_factory=list)
    team_weaknesses: List[str] = Field(default_factory=list)
    recommended_strategy: Optional[str] = None
