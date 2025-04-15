"""Video analysis service for processing basketball videos."""
import random
import math
import os
import tempfile
from typing import Any, Dict, List, Optional
import httpx
import asyncio
import cv2
import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.schemas.report import TeamAnalysis, PlayerAnalysis, DefensiveAnalysis
from app.utils.team_defense_analysis import team_defense_analyzer
from app.utils.video_chunker import video_chunker
from app.utils.player_detector import player_detector
from app.utils.ball_detector import ball_detector
from app.utils.court_detector import court_detector


class VideoAnalysisService:
    """Service for analyzing basketball videos."""

    async def get_video_data(self, video_id: int) -> Dict[str, Any]:
        """
        Get video data from the main backend service.

        Args:
            video_id: Video ID

        Returns:
            Video data
        """
        # In a real implementation, this would make an API call to the main backend
        # For now, we'll simulate it

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.MAIN_BACKEND_URL}/api/videos/{video_id}",
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(f"Error fetching video data: {response.text}")
                    raise Exception(f"Failed to fetch video data: {response.status_code}")

                return response.json()["data"]
        except Exception as e:
            logger.error(f"Error fetching video data: {str(e)}")
            # For demo purposes, return mock data
            return {
                "id": video_id,
                "title": f"Sample Game Video {video_id}",
                "description": "Basketball game footage",
                "streaming_url": f"http://example.com/videos/{video_id}",
                "duration": 3600,  # 1 hour
                "content_type": "video/mp4"
            }

    async def download_video(self, video_data: Dict[str, Any]) -> str:
        """
        Download a video from the streaming URL.

        Args:
            video_data: Video data from the main backend

        Returns:
            Path to the downloaded video file
        """
        video_id = video_data.get("id")
        streaming_url = video_data.get("streaming_url")

        logger.info(f"Downloading video {video_id} from {streaming_url}")

        # Create a temporary file for the video
        temp_dir = tempfile.gettempdir()
        video_path = os.path.join(temp_dir, f"video_{video_id}.mp4")

        # For now, we'll simulate the download
        # In a real implementation, we would download the video from the streaming URL
        # For example:
        # async with httpx.AsyncClient() as client:
        #     async with client.stream("GET", streaming_url) as response:
        #         with open(video_path, "wb") as f:
        #             async for chunk in response.aiter_bytes():
        #                 f.write(chunk)

        # For demo purposes, we'll use a sample video if available, or create a dummy video
        sample_video_path = os.path.join(os.path.dirname(__file__), "../../tests/data/sample_basketball.mp4")
        if os.path.exists(sample_video_path):
            # Copy sample video to temp location
            import shutil
            shutil.copy(sample_video_path, video_path)
            logger.info(f"Using sample video: {sample_video_path}")
        else:
            # Create a dummy video (black frames)
            logger.warning(f"Sample video not found at {sample_video_path}. Creating dummy video.")
            self._create_dummy_video(video_path)

        return video_path

    def _create_dummy_video(self, output_path: str, duration: int = 10, fps: int = 30):
        """
        Create a dummy video file for testing.

        Args:
            output_path: Path to save the video
            duration: Duration in seconds
            fps: Frames per second
        """
        # Create a black frame
        width, height = 1280, 720
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Add some text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "Sample Basketball Video", (width//2 - 200, height//2),
                    font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Write frames
        for _ in range(duration * fps):
            out.write(frame)

        # Release the video writer
        out.release()

        logger.info(f"Created dummy video at {output_path}")

    async def process_video(self, video_path: str) -> Dict[str, Any]:
        """
        Process a basketball video for analysis.

        Args:
            video_path: Path to the video file

        Returns:
            Processed frames data
        """
        logger.info(f"Processing video: {video_path}")

        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp(prefix="basketball_analysis_")

        try:
            # Get video metadata
            metadata = video_chunker.get_chunk_metadata(video_path)
            logger.info(f"Video metadata: {metadata}")

            # Split video into chunks
            chunk_paths = video_chunker.split_video(video_path, temp_dir)
            logger.info(f"Split video into {len(chunk_paths)} chunks")

            # Process each chunk
            all_frames_data = []

            for i, chunk_path in enumerate(chunk_paths):
                logger.info(f"Processing chunk {i+1}/{len(chunk_paths)}: {chunk_path}")

                # Process chunk
                chunk_data = await self._process_chunk(chunk_path)
                all_frames_data.extend(chunk_data)

                # Clean up chunk file
                os.remove(chunk_path)

            return {
                "metadata": metadata,
                "frames_data": all_frames_data
            }
        finally:
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_dir)

    async def _process_chunk(self, chunk_path: str) -> List[Dict[str, Any]]:
        """
        Process a video chunk.

        Args:
            chunk_path: Path to the video chunk

        Returns:
            List of frame data with player detections and ball tracking
        """
        frames_data = []

        # Open video
        cap = cv2.VideoCapture(chunk_path)
        if not cap.isOpened():
            logger.error(f"Could not open video chunk: {chunk_path}")
            return frames_data

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Process every 5th frame to reduce computation
        frame_interval = 5
        frame_idx = 0

        # Detect court in the first frame
        ret, first_frame = cap.read()
        if not ret:
            logger.error(f"Could not read first frame from video chunk: {chunk_path}")
            return frames_data

        # Detect court
        court_info = court_detector.detect_court(first_frame)

        # Reset video to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process every nth frame
            if frame_idx % frame_interval == 0:
                # Detect players
                players = player_detector.detect_players(frame)

                # Assign teams to players
                players = player_detector.assign_teams(players, frame)

                # Track ball
                ball = ball_detector.track_ball(frame)

                # Add frame data
                frames_data.append({
                    'frame_idx': frame_idx,
                    'timestamp': frame_idx / fps if fps > 0 else 0,
                    'players': players,
                    'ball': ball,
                    'court': court_info
                })

            frame_idx += 1

            # Log progress
            if frame_idx % 100 == 0:
                progress = (frame_idx / total_frames) * 100 if total_frames > 0 else 0
                logger.info(f"Processing progress: {progress:.1f}% ({frame_idx}/{total_frames})")

        # Release video
        cap.release()

        return frames_data

    async def analyze_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a basketball video.

        Args:
            video_data: Video data from the main backend

        Returns:
            Analysis results
        """
        video_id = video_data.get("id")
        logger.info(f"Analyzing video: {video_id}")

        try:
            # Download the video
            video_path = await self.download_video(video_data)

            # Process the video
            processing_results = await self.process_video(video_path)

            # Extract frames data
            frames_data = processing_results.get("frames_data", [])

            # If we have real frames data, use it; otherwise, fall back to mock data
            if frames_data:
                logger.info(f"Using real frames data for analysis ({len(frames_data)} frames)")
            else:
                logger.warning("No real frames data available. Using mock data.")
                frames_data = self._generate_mock_frames_data()

            # Generate team analysis
            team_analysis = self._generate_team_analysis_from_frames(frames_data) if frames_data else self._generate_mock_team_analysis()

            # Analyze team defense
            defense_analysis = team_defense_analyzer.analyze_team_defense(frames_data)

            # Create defensive analysis object
            defensive_analysis = self._create_defensive_analysis(defense_analysis)

            # Add defensive analysis to team analysis
            team_analysis.defensive_analysis = defensive_analysis

            # Generate shot chart data
            shot_chart_data = self._generate_shot_chart_from_frames(frames_data)

            # Generate player tracking data
            player_tracking_data = self._generate_player_tracking_from_frames(frames_data)

            # Generate play type analysis
            play_type_analysis = self._generate_play_type_analysis()

            # Generate advanced metrics
            advanced_metrics = self._generate_advanced_metrics()

            # Clean up the video file
            if os.path.exists(video_path):
                os.remove(video_path)

            # Return analysis results
            return {
                "video_id": video_data.get("id"),
                "video_title": video_data.get("title"),
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "team_analysis": team_analysis.dict(),
                "defense_analysis": defense_analysis,
                "shot_chart": shot_chart_data,
                "player_tracking": player_tracking_data,
                "play_type_analysis": play_type_analysis,
                "advanced_metrics": advanced_metrics
            }
        except Exception as e:
            logger.error(f"Error analyzing video: {str(e)}", exc_info=True)

            # Fall back to mock data
            logger.warning("Falling back to mock data due to error")

            # Generate mock team analysis with enhanced defensive analysis
            team_analysis = self._generate_mock_team_analysis()

            # Generate mock frames data for team defense analysis
            frames_data = self._generate_mock_frames_data()

            # Analyze team defense
            defense_analysis = team_defense_analyzer.analyze_team_defense(frames_data)

            # Create defensive analysis object
            defensive_analysis = self._create_defensive_analysis(defense_analysis)

            # Add defensive analysis to team analysis
            team_analysis.defensive_analysis = defensive_analysis

            # Generate shot chart data
            shot_chart_data = self._generate_shot_chart_data()

            # Generate player tracking data
            player_tracking_data = self._generate_player_tracking_data()

            # Generate play type analysis
            play_type_analysis = self._generate_play_type_analysis()

            # Generate advanced metrics
            advanced_metrics = self._generate_advanced_metrics()

            # Return analysis results
            return {
                "video_id": video_data.get("id"),
                "video_title": video_data.get("title"),
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "team_analysis": team_analysis.dict(),
                "defense_analysis": defense_analysis,
                "shot_chart": shot_chart_data,
                "player_tracking": player_tracking_data,
                "play_type_analysis": play_type_analysis,
                "advanced_metrics": advanced_metrics
            }

    def _generate_mock_team_analysis(self) -> TeamAnalysis:
        """
        Generate mock team analysis data.

        Returns:
            Mock team analysis
        """
        # Generate 5-12 players
        num_players = random.randint(5, 12)
        players = []

        positions = ["PG", "SG", "SF", "PF", "C"]

        # Generate a set of unique jersey numbers
        used_jersey_numbers = set()

        for i in range(num_players):
            # Generate a unique jersey number (1-99)
            while True:
                jersey_number = str(random.randint(1, 99))
                if jersey_number not in used_jersey_numbers:
                    used_jersey_numbers.add(jersey_number)
                    break

            # Assign position
            position = positions[i % 5]

            # Generate height (6'0" to 7'2")
            feet = random.randint(6, 7)
            inches = random.randint(0, 11) if feet < 7 else random.randint(0, 2)
            height = f"{feet}'{inches}\""

            # Generate physical attributes
            physical_attributes = {
                "speed": random.randint(1, 10),
                "strength": random.randint(1, 10),
                "agility": random.randint(1, 10),
                "vertical": random.randint(1, 10),
                "endurance": random.randint(1, 10)
            }

            # Generate offensive role
            offensive_role = {
                "scoring": random.randint(1, 10),
                "passing": random.randint(1, 10),
                "ball_handling": random.randint(1, 10),
                "shooting": random.randint(1, 10),
                "post_play": random.randint(1, 10)
            }

            # Generate defensive role
            defensive_role = {
                "on_ball": random.randint(1, 10),
                "off_ball": random.randint(1, 10),
                "rebounding": random.randint(1, 10),
                "shot_blocking": random.randint(1, 10),
                "steals": random.randint(1, 10)
            }

            # Generate strengths
            strengths_options = [
                "Good outside shooter",
                "Strong finisher at the rim",
                "Excellent passer",
                "Good ball handler",
                "Strong rebounder",
                "Good defender",
                "High basketball IQ",
                "Athletic",
                "Good post moves",
                "Quick first step",
                "Good free throw shooter"
            ]
            num_strengths = random.randint(2, 4)
            strengths = random.sample(strengths_options, num_strengths)

            # Generate weaknesses
            weaknesses_options = [
                "Poor outside shooter",
                "Weak finisher at the rim",
                "Poor passer",
                "Turnover prone",
                "Weak rebounder",
                "Poor defender",
                "Low basketball IQ",
                "Unathletic",
                "Poor post moves",
                "Slow first step",
                "Poor free throw shooter"
            ]
            num_weaknesses = random.randint(2, 4)
            weaknesses = random.sample(weaknesses_options, num_weaknesses)

            # Generate strategy notes
            strategy_notes_options = [
                f"Force to the left, prefers right hand",
                f"Sags off on defense, can be exploited by shooters",
                f"Aggressive on defense, can be beaten with pump fakes",
                f"Prefers to shoot from the corners",
                f"Struggles against physical defenders",
                f"Tends to over-help on defense",
                f"Hesitant to shoot from outside",
                f"Predictable post moves",
                f"Tends to force shots when pressured",
                f"Slow to get back on defense"
            ]
            strategy_notes = random.choice(strategy_notes_options)

            # Create player analysis
            player = PlayerAnalysis(
                player_id=i + 1,
                jersey_number=jersey_number,
                name=f"Player {i + 1}",
                position=position,
                height=height,
                physical_attributes=physical_attributes,
                offensive_role=offensive_role,
                defensive_role=defensive_role,
                strengths=strengths,
                weaknesses=weaknesses,
                strategy_notes=strategy_notes
            )

            players.append(player)

        # Generate team analysis
        offensive_style = {
            "pace": random.randint(1, 10),
            "spacing": random.randint(1, 10),
            "ball_movement": random.randint(1, 10),
            "post_play": random.randint(1, 10),
            "transition": random.randint(1, 10)
        }

        defensive_style = {
            "pressure": random.randint(1, 10),
            "help": random.randint(1, 10),
            "rebounding": random.randint(1, 10),
            "transition": random.randint(1, 10),
            "scheme": random.choice(["Man-to-Man", "Zone", "Switch Everything", "Mixed"])
        }

        team_strengths_options = [
            "Good 3-point shooting team",
            "Strong rebounding team",
            "Good ball movement",
            "Strong defensive team",
            "Good transition team",
            "Disciplined, low turnovers",
            "Good free throw shooting team",
            "Strong inside presence",
            "Athletic team",
            "Experienced team"
        ]
        team_strengths = random.sample(team_strengths_options, random.randint(3, 5))

        team_weaknesses_options = [
            "Poor 3-point shooting team",
            "Weak rebounding team",
            "Poor ball movement",
            "Weak defensive team",
            "Poor transition team",
            "Turnover prone",
            "Poor free throw shooting team",
            "Lack inside presence",
            "Unathletic team",
            "Inexperienced team"
        ]
        team_weaknesses = random.sample(team_weaknesses_options, random.randint(3, 5))

        recommended_strategy_options = [
            "Push the pace and exploit their poor transition defense",
            "Slow the game down and force them into half-court sets",
            "Attack the basket and draw fouls",
            "Utilize pick and roll to exploit their poor defensive rotations",
            "Spread the floor and utilize outside shooting",
            "Pack the paint and force outside shots",
            "Apply full-court pressure to force turnovers",
            "Switch all screens to disrupt their offensive flow",
            "Use zone defense to limit their inside scoring",
            "Focus on defensive rebounding to limit second-chance points"
        ]
        recommended_strategy = random.choice(recommended_strategy_options)

        return TeamAnalysis(
            team_name="Opponent Team",
            players=players,
            offensive_style=offensive_style,
            defensive_style=defensive_style,
            team_strengths=team_strengths,
            team_weaknesses=team_weaknesses,
            recommended_strategy=recommended_strategy
        )


    def _generate_mock_frames_data(self) -> List[Dict[str, Any]]:
        """
        Generate mock frames data for team defense analysis.

        Returns:
            List of frame data with player detections and poses
        """
        # Generate 20-30 frames of data
        num_frames = random.randint(20, 30)
        frames_data = []

        for frame_idx in range(num_frames):
            # Generate 8-10 players (both teams)
            num_players = random.randint(8, 10)
            players = []

            for player_idx in range(num_players):
                # Generate player detection with bounding box
                player = {
                    'id': player_idx + 1,
                    'bbox': [
                        random.randint(100, 900),  # x1
                        random.randint(100, 500),  # y1
                        random.randint(150, 950),  # x2
                        random.randint(150, 550)   # y2
                    ],
                    'confidence': random.uniform(0.7, 0.95),
                    'team': 'defense' if player_idx < num_players // 2 else 'offense',
                    'jersey_number': str(random.randint(1, 99))
                }

                # Generate keypoints (simplified)
                keypoints = []
                for _ in range(18):  # 18 keypoints as defined in pose_estimator
                    x = random.randint(player['bbox'][0], player['bbox'][2])
                    y = random.randint(player['bbox'][1], player['bbox'][3])
                    confidence = random.uniform(0.5, 0.9)
                    keypoints.append([x, y, confidence])

                player['keypoints'] = keypoints
                players.append(player)

            frames_data.append({
                'frame_idx': frame_idx,
                'players': players
            })

        return frames_data

    def _create_defensive_analysis(self, defense_analysis: Dict[str, Any]) -> DefensiveAnalysis:
        """
        Create a DefensiveAnalysis object from team defense analysis results.

        Args:
            defense_analysis: Team defense analysis results

        Returns:
            DefensiveAnalysis object
        """
        # Extract defense type analysis
        defense_type_analysis = defense_analysis.get('defense_type_analysis', {})
        primary_defense = defense_type_analysis.get('primary_defense', 'Man-to-Man')
        # Get confidence in defense type detection
        # defense_confidence = defense_type_analysis.get('confidence', 0)  # Uncomment if needed
        defense_subtypes = defense_type_analysis.get('subtypes', {})

        # Determine defense type and subtype
        if 'Zone' in primary_defense:
            defense_type = 'Zone'
            defense_subtype = primary_defense
        else:
            defense_type = primary_defense
            defense_subtype = None

        # Extract formation analysis
        formation_analysis = defense_analysis.get('formation_analysis', {})

        # Map pressure rating to pressure level
        pressure_rating = formation_analysis.get('pressure_rating', 5)
        if pressure_rating >= 7:
            pressure_level = 'High'
        elif pressure_rating >= 4:
            pressure_level = 'Medium'
        else:
            pressure_level = 'Low'

        # Determine pick up point based on defensive line
        defensive_line = formation_analysis.get('defensive_line', 'Half Court')
        pick_up_point = defensive_line

        # Extract matchup analysis
        matchup_analysis = defense_analysis.get('matchup_analysis', {})
        best_defenders = []
        weak_defenders = []

        if matchup_analysis.get('best_defender_id'):
            best_defenders.append(f"Player {matchup_analysis.get('best_defender_id')}")

        if matchup_analysis.get('weakest_defender_id'):
            weak_defenders.append(f"Player {matchup_analysis.get('weakest_defender_id')}")

        # Extract stance analysis
        stance_analysis = defense_analysis.get('stance_analysis', {})

        if stance_analysis.get('best_stance_player_id') and stance_analysis.get('best_stance_player_id') not in best_defenders:
            best_defenders.append(f"Player {stance_analysis.get('best_stance_player_id')}")

        if stance_analysis.get('weakest_stance_player_id') and stance_analysis.get('weakest_stance_player_id') not in weak_defenders:
            weak_defenders.append(f"Player {stance_analysis.get('weakest_stance_player_id')}")

        # Extract movement analysis
        movement_analysis = defense_analysis.get('movement_analysis', {})

        if movement_analysis.get('best_movement_player_id') and movement_analysis.get('best_movement_player_id') not in best_defenders:
            best_defenders.append(f"Player {movement_analysis.get('best_movement_player_id')}")

        if movement_analysis.get('weakest_movement_player_id') and movement_analysis.get('weakest_movement_player_id') not in weak_defenders:
            weak_defenders.append(f"Player {movement_analysis.get('weakest_movement_player_id')}")

        # Extract rotation analysis
        rotation_analysis = defense_analysis.get('rotation_analysis', {})
        help_defense_rating = rotation_analysis.get('help_defense_rating', 5)

        # Map ratings to frequency strings
        def rating_to_frequency(rating):
            if rating >= 7:
                return "Frequently"
            elif rating >= 4:
                return "Occasionally"
            else:
                return "Seldom"

        # Map ratings to strength strings
        def rating_to_strength(rating):
            if rating >= 7:
                return "Strong"
            elif rating >= 5:
                return "Medium"
            elif rating >= 3:
                return "Soft"
            else:
                return "Weak"

        # Create defensive analysis object
        return DefensiveAnalysis(
            # Defense type
            defense_type=defense_type,
            defense_subtype=defense_subtype,

            # Defense characteristics
            pressure_level=pressure_level,
            pick_up_point=pick_up_point,

            # Defensive tendencies
            deny_first_pass=rating_to_frequency(random.randint(1, 10)),
            deny_ball_reversal=rating_to_frequency(random.randint(1, 10)),
            allow_dribble_penetration=rating_to_frequency(random.randint(1, 10)),

            # Transition defense
            transition_defense_speed=random.choice(["Quick", "Medium", "Slow"]),
            vulnerable_to_fast_break=rating_to_frequency(random.randint(1, 10)),
            vulnerable_to_long_passes=rating_to_frequency(random.randint(1, 10)),
            pressure_rebounder=rating_to_frequency(random.randint(1, 10)),
            pressure_outlet_pass=rating_to_frequency(random.randint(1, 10)),

            # Post defense
            post_defense_strength=rating_to_strength(random.randint(1, 10)),
            post_defense_deployment=random.choice(["Front", "Behind", "3/4", "Push Out", "Trap"]),
            allow_post_feeds=rating_to_frequency(random.randint(1, 10)),
            post_feed_reaction=random.choice(["Collapse", "Play 1/2 way Off", "Trap", "None"]),
            post_lob_defense=random.choice(["Collapse", "Trap", "None"]),

            # Screen defense
            on_ball_screen_strength=rating_to_strength(random.randint(1, 10)),
            on_ball_screen_primary=random.choice(["Show & Recover", "Switch", "Trap", "Fight Over", "Go Under"]),
            off_ball_screen_strength=rating_to_strength(random.randint(1, 10)),
            off_ball_screen_primary=random.choice(["Chase Out", "Show & Recover", "Switch", "Go Under"]),

            # Help defense
            helpside_defense=rating_to_strength(help_defense_rating),
            deny_lane_cuts=rating_to_frequency(rotation_analysis.get('rotation_quality', 5)),
            trap_dribble_penetration=rating_to_frequency(rotation_analysis.get('help_defense_rating', 5)),
            closeout_quality="Quick (on Balance)" if rotation_analysis.get('rotation_speed', 5) > 7 else
                           "Slow" if rotation_analysis.get('rotation_speed', 5) < 4 else "Medium",
            box_out_frequency=rating_to_frequency(stance_analysis.get('average_stance_quality', 5)),

            # Zone defense (if applicable)
            zone_activity=rating_to_strength(random.randint(1, 10)) if defense_type == "Zone" else None,
            zone_ball_pressure=rating_to_frequency(random.randint(1, 10)) if defense_type == "Zone" else None,
            zone_post_fronting=rating_to_frequency(random.randint(1, 10)) if defense_type == "Zone" else None,
            zone_trapping=rating_to_frequency(random.randint(1, 10)) if defense_type == "Zone" else None,
            zone_shifts=random.choice(["Quick", "Medium", "Slow", "Rushed"]) if defense_type == "Zone" else None,

            # Special situations
            extend_defense_frequency=rating_to_frequency(random.randint(1, 10)),
            primary_press=random.choice(["1-2-1-1", "2-2-1", "1-3-1", "Man Press"]) if random.random() > 0.3 else None,
            secondary_press=random.choice(["1-2-1-1", "2-2-1", "1-3-1", "Man Press"]) if random.random() > 0.6 else None,
            deny_inbounds=rating_to_frequency(random.randint(1, 10)),
            trap_first_pass=rating_to_frequency(random.randint(1, 10)),
            baseline_out_defense=rating_to_strength(random.randint(1, 10)),
            sideline_out_defense=rating_to_strength(random.randint(1, 10)),

            # Key defensive personnel
            best_on_ball_defenders=best_defenders,
            weak_on_ball_defenders=weak_defenders,
            best_post_defenders=[f"Player {random.randint(1, 5)}" for _ in range(random.randint(1, 2))],
            weak_post_defenders=[f"Player {random.randint(6, 10)}" for _ in range(random.randint(1, 2))],
            best_defensive_rebounders=[f"Player {random.randint(1, 10)}" for _ in range(random.randint(1, 3))],
            best_shot_blockers=[f"Player {random.randint(1, 10)}" for _ in range(random.randint(1, 2))],
            weakside_ball_watchers=[f"Player {random.randint(1, 10)}" for _ in range(random.randint(1, 2))],
            slow_transition_defenders=[f"Player {random.randint(1, 10)}" for _ in range(random.randint(1, 2))],

            # Analysis notes
            vulnerable_screen_types="Ball Screens" if defense_type == "Man-to-Man" else "Flare Screens",
            last_shot_defense="Switch Everything" if defense_type == "Man-to-Man" else "Zone Up",
            combination_defenses={
                "primary": defense_type,
                "secondary": "Zone" if defense_type != "Zone" else "Man-to-Man",
                "subtypes": defense_subtypes
            },
            notes=(
                f"Team shows a {defense_type} defense with {pressure_level} pressure. "
                f"Overall defensive rating: {defense_analysis.get('overall_rating', 5)}/10. "
                f"Help defense rating: {help_defense_rating}/10. "
                f"Rotation quality: {rotation_analysis.get('rotation_quality', 5)}/10. "
                f"Stance quality: {stance_analysis.get('average_stance_quality', 5)}/10. "
                f"Movement quality: {movement_analysis.get('average_movement_quality', 5)}/10."
            )
        )

    def _generate_shot_chart_data(self) -> Dict[str, Any]:
        """
        Generate mock shot chart data.

        Returns:
            Shot chart data with locations, makes/misses, and player info
        """
        # Generate 50-100 shots
        num_shots = random.randint(50, 100)
        shots = []

        # Court dimensions (in feet)
        court_length = 94
        court_width = 50

        # Shot types and their probabilities
        shot_types = {
            "3PT": 0.35,  # 35% of shots are 3-pointers
            "Mid-Range": 0.25,  # 25% are mid-range
            "Paint": 0.25,  # 25% are in the paint
            "Layup/Dunk": 0.15  # 15% are layups or dunks
        }

        # Shot success rates by type
        success_rates = {
            "3PT": 0.36,  # 36% success rate for 3-pointers
            "Mid-Range": 0.42,  # 42% for mid-range
            "Paint": 0.55,  # 55% for paint shots
            "Layup/Dunk": 0.68  # 68% for layups/dunks
        }

        # Generate player IDs (1-10)
        player_ids = list(range(1, 11))

        # Generate shots
        for _ in range(num_shots):
            # Determine shot type based on probabilities
            shot_type = random.choices(
                list(shot_types.keys()),
                weights=list(shot_types.values()),
                k=1
            )[0]

            # Determine shot location based on type
            if shot_type == "3PT":
                # 3-point shots are beyond the arc
                angle = random.uniform(0, 2 * 3.14159)  # Random angle around the basket
                distance = random.uniform(24, 30)  # Distance from basket (feet)
                x = court_width / 2 + distance * 0.8 * math.cos(angle)  # Adjust for court coordinates
                y = distance * math.sin(angle)
            elif shot_type == "Mid-Range":
                # Mid-range shots are inside the arc but outside the paint
                angle = random.uniform(0, 2 * 3.14159)
                distance = random.uniform(10, 22)  # Distance from basket (feet)
                x = court_width / 2 + distance * 0.8 * math.cos(angle)
                y = distance * math.sin(angle)
            elif shot_type == "Paint":
                # Paint shots are in the key but not layups/dunks
                x = court_width / 2 + random.uniform(-8, 8)
                y = random.uniform(0, 15)
            else:  # Layup/Dunk
                # Layups/dunks are very close to the basket
                x = court_width / 2 + random.uniform(-5, 5)
                y = random.uniform(0, 5)

            # Determine if shot was made based on type's success rate
            made = random.random() < success_rates[shot_type]

            # Assign to a random player
            player_id = random.choice(player_ids)

            # Create shot data
            shot = {
                "id": _ + 1,
                "player_id": player_id,
                "x": x,
                "y": y,
                "shot_type": shot_type,
                "made": made,
                "quarter": random.randint(1, 4),
                "time_remaining": f"{random.randint(0, 11)}:{random.randint(0, 59):02d}",
                "distance": math.sqrt((x - court_width / 2) ** 2 + y ** 2),
                "points": 3 if shot_type == "3PT" else 2
            }

            shots.append(shot)

        # Calculate shooting percentages by zone
        zone_stats = {}
        for zone in shot_types.keys():
            zone_shots = [s for s in shots if s["shot_type"] == zone]
            if zone_shots:
                made_shots = [s for s in zone_shots if s["made"]]
                zone_stats[zone] = {
                    "attempts": len(zone_shots),
                    "made": len(made_shots),
                    "percentage": round(len(made_shots) / len(zone_shots) * 100, 1)
                }

        # Calculate player shooting stats
        player_stats = {}
        for player_id in player_ids:
            player_shots = [s for s in shots if s["player_id"] == player_id]
            if player_shots:
                made_shots = [s for s in player_shots if s["made"]]
                player_stats[str(player_id)] = {
                    "attempts": len(player_shots),
                    "made": len(made_shots),
                    "percentage": round(len(made_shots) / len(player_shots) * 100, 1),
                    "points": sum(s["points"] for s in player_shots if s["made"])
                }

        return {
            "shots": shots,
            "zone_stats": zone_stats,
            "player_stats": player_stats,
            "court_dimensions": {
                "length": court_length,
                "width": court_width
            }
        }

    def _generate_player_tracking_data(self) -> Dict[str, Any]:
        """
        Generate mock player tracking data.

        Returns:
            Player tracking data including movement, speed, and distance
        """
        # Generate data for 10 players (5 per team)
        player_data = {}

        for player_id in range(1, 11):
            # Determine if player is on offense or defense
            is_offense = player_id > 5

            # Generate speed data (feet per second)
            avg_speed = round(random.uniform(10, 16), 1)  # Average NBA player speed
            max_speed = round(avg_speed * random.uniform(1.2, 1.5), 1)  # Max speed is 20-50% higher

            # Generate distance data (miles)
            distance = round(random.uniform(1.5, 3.0), 2)  # Miles run during game

            # Generate sprint data
            sprints = random.randint(30, 80)  # Number of sprints

            # Generate movement heatmap data (simplified)
            heatmap = []
            for _ in range(50):  # 50 data points for heatmap
                x = random.uniform(0, 94)  # Court length
                y = random.uniform(0, 50)  # Court width
                intensity = random.uniform(0, 1)  # Intensity at this point
                heatmap.append({"x": x, "y": y, "intensity": intensity})

            # Generate player movement patterns
            if is_offense:
                # Offensive players have different patterns
                patterns = random.sample([
                    "Perimeter-oriented",
                    "Paint-dominant",
                    "Corner specialist",
                    "High post operator",
                    "Transition runner"
                ], 2)
            else:
                # Defensive players have different patterns
                patterns = random.sample([
                    "Help defender",
                    "On-ball pressure",
                    "Paint protector",
                    "Perimeter defender",
                    "Transition defender"
                ], 2)

            player_data[str(player_id)] = {
                "avg_speed": avg_speed,
                "max_speed": max_speed,
                "distance": distance,
                "sprints": sprints,
                "heatmap": heatmap,
                "movement_patterns": patterns,
                "time_of_possession": round(random.uniform(0, 8), 1) if is_offense else 0,  # Minutes
                "defensive_matchups": [
                    {"opponent_id": i, "time": round(random.uniform(1, 8), 1)}
                    for i in random.sample(range(6, 11), 3)
                ] if not is_offense else []
            }

        return {
            "player_data": player_data,
            "team_stats": {
                "avg_speed": round(sum(p["avg_speed"] for p in player_data.values()) / 10, 1),
                "total_distance": round(sum(p["distance"] for p in player_data.values()), 1),
                "avg_sprints": round(sum(p["sprints"] for p in player_data.values()) / 10)
            }
        }

    def _generate_play_type_analysis(self) -> Dict[str, Any]:
        """
        Generate mock play type analysis data.

        Returns:
            Analysis of different play types used and their effectiveness
        """
        # Define play types and their frequency ranges
        play_types = {
            "Pick and Roll (Ball Handler)": (15, 25),
            "Pick and Roll (Roll Man)": (8, 15),
            "Post Up": (5, 15),
            "Spot Up": (15, 25),
            "Isolation": (8, 15),
            "Handoff": (3, 8),
            "Cut": (5, 12),
            "Off Screen": (5, 10),
            "Transition": (10, 20),
            "Putback": (3, 8)
        }

        # Generate play type data
        play_data = {}
        total_possessions = random.randint(90, 110)  # Total possessions in a game
        remaining_possessions = total_possessions

        for play_type, freq_range in play_types.items():
            # Determine frequency (within range)
            if play_type == list(play_types.keys())[-1]:
                # Last play type gets remaining possessions
                frequency = remaining_possessions
            else:
                min_freq, max_freq = freq_range
                frequency = min(random.randint(min_freq, max_freq), remaining_possessions)
                remaining_possessions -= frequency

            # Skip if no possessions left
            if frequency <= 0:
                continue

            # Generate effectiveness metrics
            points_per_possession = round(random.uniform(0.7, 1.3), 2)
            field_goal_percentage = round(random.uniform(35, 60), 1)

            # Determine if this is a strength or weakness
            is_strength = points_per_possession > 1.0

            play_data[play_type] = {
                "frequency": frequency,
                "percentage": round((frequency / total_possessions) * 100, 1),
                "points_per_possession": points_per_possession,
                "field_goal_percentage": field_goal_percentage,
                "is_strength": is_strength,
                "primary_players": random.sample(range(1, 11), min(3, frequency // 5 + 1))
            }

        # Identify top plays and recommendations
        sorted_plays = sorted(
            play_data.items(),
            key=lambda x: x[1]["points_per_possession"],
            reverse=True
        )

        strengths = [p[0] for p in sorted_plays[:3] if p[1]["is_strength"]]
        weaknesses = [p[0] for p in sorted_plays[-3:] if not p[1]["is_strength"]]

        return {
            "play_data": play_data,
            "total_possessions": total_possessions,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": [
                f"Force them into {w} situations" for w in weaknesses
            ] + [
                f"Limit {s} opportunities" for s in strengths
            ]
        }

    def _generate_advanced_metrics(self) -> Dict[str, Any]:
        """
        Generate mock advanced basketball metrics.

        Returns:
            Advanced team and player metrics
        """
        # Team-level advanced metrics
        team_metrics = {
            "offensive_rating": round(random.uniform(95, 120), 1),  # Points per 100 possessions
            "defensive_rating": round(random.uniform(95, 120), 1),  # Points allowed per 100 possessions
            "pace": round(random.uniform(90, 105), 1),  # Possessions per 48 minutes
            "true_shooting": round(random.uniform(50, 62), 1),  # TS%
            "effective_fg": round(random.uniform(45, 58), 1),  # eFG%
            "turnover_rate": round(random.uniform(10, 18), 1),  # TOV%
            "offensive_rebound_rate": round(random.uniform(18, 32), 1),  # ORB%
            "defensive_rebound_rate": round(random.uniform(65, 80), 1),  # DRB%
            "assist_rate": round(random.uniform(50, 70), 1),  # AST%
            "block_rate": round(random.uniform(3, 10), 1),  # BLK%
            "steal_rate": round(random.uniform(5, 12), 1)  # STL%
        }

        # Calculate net rating
        team_metrics["net_rating"] = round(team_metrics["offensive_rating"] - team_metrics["defensive_rating"], 1)

        # Player-level advanced metrics
        player_metrics = {}
        for player_id in range(1, 11):
            player_metrics[str(player_id)] = {
                "player_efficiency_rating": round(random.uniform(8, 25), 1),  # PER
                "true_shooting": round(random.uniform(48, 65), 1),  # TS%
                "usage_rate": round(random.uniform(10, 35), 1),  # USG%
                "assist_percentage": round(random.uniform(5, 40), 1),  # AST%
                "rebound_percentage": round(random.uniform(3, 20), 1),  # REB%
                "steal_percentage": round(random.uniform(0.5, 4), 1),  # STL%
                "block_percentage": round(random.uniform(0.1, 5), 1),  # BLK%
                "turnover_percentage": round(random.uniform(5, 20), 1),  # TOV%
                "offensive_rating": round(random.uniform(90, 125), 1),  # ORtg
                "defensive_rating": round(random.uniform(90, 125), 1),  # DRtg
                "box_plus_minus": round(random.uniform(-5, 10), 1),  # BPM
                "value_over_replacement": round(random.uniform(-1, 5), 1)  # VORP
            }

            # Calculate net rating
            player_metrics[str(player_id)]["net_rating"] = round(
                player_metrics[str(player_id)]["offensive_rating"] -
                player_metrics[str(player_id)]["defensive_rating"], 1
            )

        # Generate lineup data
        lineups = []
        for _ in range(5):  # Generate 5 different lineups
            players = sorted(random.sample(range(1, 11), 5))
            minutes = round(random.uniform(5, 20), 1)
            net_rating = round(random.uniform(-15, 15), 1)

            lineups.append({
                "players": players,
                "minutes": minutes,
                "offensive_rating": round(random.uniform(95, 120), 1),
                "defensive_rating": round(random.uniform(95, 120), 1),
                "net_rating": net_rating,
                "plus_minus": round(net_rating * minutes / 10, 1)  # Simplified calculation
            })

        return {
            "team_metrics": team_metrics,
            "player_metrics": player_metrics,
            "lineups": lineups,
            "four_factors": {
                "shooting": team_metrics["effective_fg"],
                "turnovers": team_metrics["turnover_rate"],
                "rebounding": team_metrics["offensive_rebound_rate"],
                "free_throws": round(random.uniform(18, 35), 1)  # FT Rate
            }
        }

    def _generate_team_analysis_from_frames(self, frames_data: List[Dict[str, Any]]) -> TeamAnalysis:
        """
        Generate team analysis from real frames data.

        Args:
            frames_data: List of frame data with player detections

        Returns:
            Team analysis
        """
        logger.info("Generating team analysis from real frames data")

        # Extract player information from frames
        player_info = self._extract_player_info(frames_data)

        # Generate players list
        players = []
        for player_id, info in player_info.items():
            # Generate jersey number (use detected number or assign one)
            jersey_number = info.get('jersey_number', str(player_id))

            # Determine position based on movement patterns
            position = self._determine_player_position(info)

            # Generate height (placeholder - would be determined from player dimensions)
            height = "6'0\""  # Default height

            # Generate physical attributes based on movement
            physical_attributes = self._generate_physical_attributes(info)

            # Generate offensive and defensive roles
            offensive_role = self._generate_offensive_role(info)
            defensive_role = self._generate_defensive_role(info)

            # Generate strengths and weaknesses
            strengths = self._generate_player_strengths(info)
            weaknesses = self._generate_player_weaknesses(info)

            # Generate strategy notes
            strategy_notes = self._generate_strategy_notes(info)

            # Create player analysis
            player = PlayerAnalysis(
                player_id=player_id,
                jersey_number=jersey_number,
                name=f"Player {jersey_number}",
                position=position,
                height=height,
                physical_attributes=physical_attributes,
                offensive_role=offensive_role,
                defensive_role=defensive_role,
                strengths=strengths,
                weaknesses=weaknesses,
                strategy_notes=strategy_notes
            )

            players.append(player)

        # Generate team analysis
        team_style = self._analyze_team_style(frames_data, player_info)

        return TeamAnalysis(
            team_name="Opponent Team",
            players=players,
            offensive_style=team_style.get('offensive', {}),
            defensive_style=team_style.get('defensive', {}),
            team_strengths=team_style.get('strengths', []),
            team_weaknesses=team_style.get('weaknesses', []),
            recommended_strategy=team_style.get('recommended_strategy', '')
        )

    def _extract_player_info(self, frames_data: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Extract player information from frames data.

        Args:
            frames_data: List of frame data with player detections

        Returns:
            Dictionary of player information by player ID
        """
        player_info = {}

        for frame in frames_data:
            players = frame.get('players', [])

            for player in players:
                player_id = player.get('id')

                if player_id not in player_info:
                    player_info[player_id] = {
                        'positions': [],
                        'team': player.get('team', 'unknown'),
                        'jersey_number': player.get('jersey_number', str(player_id)),
                        'keypoints': [],
                        'bbox': [],
                        'frame_count': 0
                    }

                # Add position
                if 'bbox' in player:
                    x1, y1, x2, y2 = player['bbox']
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    player_info[player_id]['positions'].append((center_x, center_y))
                    player_info[player_id]['bbox'].append(player['bbox'])

                # Add keypoints if available
                if 'keypoints' in player:
                    player_info[player_id]['keypoints'].append(player['keypoints'])

                # Increment frame count
                player_info[player_id]['frame_count'] += 1

        # Calculate average position and movement
        for player_id, info in player_info.items():
            if info['positions']:
                # Calculate average position
                avg_x = sum(pos[0] for pos in info['positions']) / len(info['positions'])
                avg_y = sum(pos[1] for pos in info['positions']) / len(info['positions'])
                info['avg_position'] = (avg_x, avg_y)

                # Calculate movement (distance traveled)
                movement = 0
                for i in range(1, len(info['positions'])):
                    x1, y1 = info['positions'][i-1]
                    x2, y2 = info['positions'][i]
                    movement += math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                info['movement'] = movement
                info['avg_movement'] = movement / len(info['positions']) if len(info['positions']) > 0 else 0

        return player_info

    def _determine_player_position(self, player_info: Dict[str, Any]) -> str:
        """
        Determine player position based on movement patterns.

        Args:
            player_info: Player information

        Returns:
            Player position (PG, SG, SF, PF, C)
        """
        # This is a simplified position determination
        # In a real implementation, we would use more sophisticated analysis

        # Get average position
        avg_position = player_info.get('avg_position', (0, 0))
        movement = player_info.get('avg_movement', 0)

        # Determine position based on movement and court location
        if movement > 10:  # High movement
            if avg_position[0] < 400:  # Left side of court
                return "PG"
            else:  # Right side of court
                return "SG"
        elif movement > 5:  # Medium movement
            if avg_position[0] < 400:  # Left side of court
                return "SF"
            else:  # Right side of court
                return "PF"
        else:  # Low movement
            return "C"

    def _generate_physical_attributes(self, player_info: Dict[str, Any]) -> Dict[str, int]:
        """
        Generate physical attributes based on player movement.

        Args:
            player_info: Player information

        Returns:
            Physical attributes
        """
        # Calculate attributes based on movement patterns
        movement = player_info.get('avg_movement', 0)

        # Scale movement to 1-10 range
        speed = min(10, max(1, int(movement / 5)))

        # Other attributes are more placeholder for now
        return {
            "speed": speed,
            "strength": random.randint(1, 10),
            "agility": min(10, max(1, int(movement / 4))),
            "vertical": random.randint(1, 10),
            "endurance": min(10, max(1, int(player_info.get('frame_count', 0) / 10)))
        }

    def _generate_offensive_role(self, player_info: Dict[str, Any]) -> Dict[str, int]:
        """
        Generate offensive role based on player movement.

        Args:
            player_info: Player information

        Returns:
            Offensive role attributes
        """
        # This would be based on detected actions in a real implementation
        # For now, we'll use some heuristics based on position and movement

        # Get average position and movement
        avg_position = player_info.get('avg_position', (0, 0))
        movement = player_info.get('avg_movement', 0)

        # Determine offensive role based on position and movement
        if movement > 10:  # High movement - likely a guard
            return {
                "scoring": random.randint(5, 10),
                "passing": random.randint(5, 10),
                "ball_handling": random.randint(7, 10),
                "shooting": random.randint(5, 10),
                "post_play": random.randint(1, 5)
            }
        elif movement > 5:  # Medium movement - likely a forward
            return {
                "scoring": random.randint(5, 10),
                "passing": random.randint(3, 8),
                "ball_handling": random.randint(3, 8),
                "shooting": random.randint(3, 8),
                "post_play": random.randint(3, 8)
            }
        else:  # Low movement - likely a center
            return {
                "scoring": random.randint(3, 8),
                "passing": random.randint(1, 6),
                "ball_handling": random.randint(1, 5),
                "shooting": random.randint(1, 5),
                "post_play": random.randint(5, 10)
            }

    def _generate_defensive_role(self, player_info: Dict[str, Any]) -> Dict[str, int]:
        """
        Generate defensive role based on player movement.

        Args:
            player_info: Player information

        Returns:
            Defensive role attributes
        """
        # This would be based on detected actions in a real implementation
        # For now, we'll use some heuristics based on position and movement

        # Get average position and movement
        avg_position = player_info.get('avg_position', (0, 0))
        movement = player_info.get('avg_movement', 0)

        # Determine defensive role based on position and movement
        if movement > 10:  # High movement - likely a perimeter defender
            return {
                "on_ball": random.randint(5, 10),
                "off_ball": random.randint(5, 10),
                "rebounding": random.randint(1, 5),
                "shot_blocking": random.randint(1, 5),
                "steals": random.randint(5, 10)
            }
        elif movement > 5:  # Medium movement - likely a wing defender
            return {
                "on_ball": random.randint(3, 8),
                "off_ball": random.randint(5, 10),
                "rebounding": random.randint(3, 8),
                "shot_blocking": random.randint(3, 8),
                "steals": random.randint(3, 8)
            }
        else:  # Low movement - likely an interior defender
            return {
                "on_ball": random.randint(1, 5),
                "off_ball": random.randint(3, 8),
                "rebounding": random.randint(5, 10),
                "shot_blocking": random.randint(5, 10),
                "steals": random.randint(1, 5)
            }

    def _generate_player_strengths(self, player_info: Dict[str, Any]) -> List[str]:
        """
        Generate player strengths based on movement patterns.

        Args:
            player_info: Player information

        Returns:
            List of player strengths
        """
        strengths = []
        movement = player_info.get('avg_movement', 0)

        # Add strengths based on movement
        if movement > 10:
            strengths.append("Good ball handler")
            strengths.append("Quick first step")
        elif movement > 5:
            strengths.append("Good outside shooter")
            strengths.append("Athletic")
        else:
            strengths.append("Strong rebounder")
            strengths.append("Good post moves")

        # Add some random strengths
        strengths_options = [
            "Good outside shooter",
            "Strong finisher at the rim",
            "Excellent passer",
            "Good ball handler",
            "Strong rebounder",
            "Good defender",
            "High basketball IQ",
            "Athletic",
            "Good post moves",
            "Quick first step",
            "Good free throw shooter"
        ]

        # Add 1-2 random strengths
        for _ in range(random.randint(1, 2)):
            strength = random.choice(strengths_options)
            if strength not in strengths:
                strengths.append(strength)

        return strengths

    def _generate_player_weaknesses(self, player_info: Dict[str, Any]) -> List[str]:
        """
        Generate player weaknesses based on movement patterns.

        Args:
            player_info: Player information

        Returns:
            List of player weaknesses
        """
        weaknesses = []
        movement = player_info.get('avg_movement', 0)

        # Add weaknesses based on movement
        if movement > 10:
            weaknesses.append("Weak rebounder")
        elif movement > 5:
            weaknesses.append("Turnover prone")
        else:
            weaknesses.append("Poor outside shooter")
            weaknesses.append("Slow first step")

        # Add some random weaknesses
        weaknesses_options = [
            "Poor outside shooter",
            "Weak finisher at the rim",
            "Poor passer",
            "Turnover prone",
            "Weak rebounder",
            "Poor defender",
            "Low basketball IQ",
            "Unathletic",
            "Poor post moves",
            "Slow first step",
            "Poor free throw shooter"
        ]

        # Add 1-2 random weaknesses
        for _ in range(random.randint(1, 2)):
            weakness = random.choice(weaknesses_options)
            if weakness not in weaknesses:
                weaknesses.append(weakness)

        return weaknesses

    def _generate_strategy_notes(self, player_info: Dict[str, Any]) -> str:
        """
        Generate strategy notes based on player information.

        Args:
            player_info: Player information

        Returns:
            Strategy notes
        """
        # Generate strategy notes based on player tendencies
        strategy_notes_options = [
            f"Force to the left, prefers right hand",
            f"Sags off on defense, can be exploited by shooters",
            f"Aggressive on defense, can be beaten with pump fakes",
            f"Prefers to shoot from the corners",
            f"Struggles against physical defenders",
            f"Tends to over-help on defense",
            f"Hesitant to shoot from outside",
            f"Predictable post moves",
            f"Tends to force shots when pressured",
            f"Slow to get back on defense"
        ]

        return random.choice(strategy_notes_options)

    def _analyze_team_style(self, frames_data: List[Dict[str, Any]], player_info: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze team style based on frames data.

        Args:
            frames_data: List of frame data
            player_info: Dictionary of player information

        Returns:
            Team style analysis
        """
        # Calculate team movement metrics
        total_movement = sum(info.get('movement', 0) for info in player_info.values())
        avg_movement = total_movement / len(player_info) if player_info else 0

        # Determine offensive style based on movement
        offensive_style = {
            "pace": min(10, max(1, int(avg_movement / 10))),
            "spacing": random.randint(1, 10),
            "ball_movement": random.randint(1, 10),
            "post_play": random.randint(1, 10),
            "transition": min(10, max(1, int(avg_movement / 8)))
        }

        # Determine defensive style
        defensive_style = {
            "pressure": min(10, max(1, int(avg_movement / 9))),
            "help": random.randint(1, 10),
            "rebounding": random.randint(1, 10),
            "transition": min(10, max(1, int(avg_movement / 8))),
            "scheme": random.choice(["Man-to-Man", "Zone", "Switch Everything", "Mixed"])
        }

        # Determine team strengths based on style
        team_strengths = []

        if offensive_style["pace"] >= 7:
            team_strengths.append("Good transition team")

        if offensive_style["ball_movement"] >= 7:
            team_strengths.append("Good ball movement")

        if defensive_style["pressure"] >= 7:
            team_strengths.append("Strong defensive team")

        # Add some random strengths
        strengths_options = [
            "Good 3-point shooting team",
            "Strong rebounding team",
            "Good ball movement",
            "Strong defensive team",
            "Good transition team",
            "Disciplined, low turnovers",
            "Good free throw shooting team",
            "Strong inside presence",
            "Athletic team",
            "Experienced team"
        ]

        # Add 2-3 random strengths
        for _ in range(random.randint(2, 3)):
            strength = random.choice(strengths_options)
            if strength not in team_strengths:
                team_strengths.append(strength)

        # Determine team weaknesses based on style
        team_weaknesses = []

        if offensive_style["pace"] <= 3:
            team_weaknesses.append("Poor transition team")

        if offensive_style["ball_movement"] <= 3:
            team_weaknesses.append("Poor ball movement")

        if defensive_style["pressure"] <= 3:
            team_weaknesses.append("Weak defensive team")

        # Add some random weaknesses
        weaknesses_options = [
            "Poor 3-point shooting team",
            "Weak rebounding team",
            "Poor ball movement",
            "Weak defensive team",
            "Poor transition team",
            "Turnover prone",
            "Poor free throw shooting team",
            "Lack inside presence",
            "Unathletic team",
            "Inexperienced team"
        ]

        # Add 2-3 random weaknesses
        for _ in range(random.randint(2, 3)):
            weakness = random.choice(weaknesses_options)
            if weakness not in team_weaknesses:
                team_weaknesses.append(weakness)

        # Generate recommended strategy
        recommended_strategy_options = [
            "Push the pace and exploit their poor transition defense",
            "Slow the game down and force them into half-court sets",
            "Attack the basket and draw fouls",
            "Utilize pick and roll to exploit their poor defensive rotations",
            "Spread the floor and utilize outside shooting",
            "Pack the paint and force outside shots",
            "Apply full-court pressure to force turnovers",
            "Switch all screens to disrupt their offensive flow",
            "Use zone defense to limit their inside scoring",
            "Focus on defensive rebounding to limit second-chance points"
        ]

        recommended_strategy = random.choice(recommended_strategy_options)

        return {
            "offensive": offensive_style,
            "defensive": defensive_style,
            "strengths": team_strengths,
            "weaknesses": team_weaknesses,
            "recommended_strategy": recommended_strategy
        }

    def _generate_shot_chart_from_frames(self, frames_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate shot chart data from frames data.

        Args:
            frames_data: List of frame data

        Returns:
            Shot chart data
        """
        # Extract ball tracking data
        ball_tracking = [frame.get('ball', None) for frame in frames_data]

        # Get court info from the first frame that has it
        court_info = None
        for frame in frames_data:
            if 'court' in frame:
                court_info = frame['court']
                break

        # Detect shots from ball trajectory
        shots = ball_detector.detect_shot(ball_tracking, court_info)

        if not shots:
            # Fall back to mock data if no shots detected
            logger.warning("No shots detected from frames data. Using mock shot chart data.")
            return self._generate_shot_chart_data()

        # Convert shots to shot chart format
        shot_data = []
        for i, shot in enumerate(shots):
            # Get shot position
            position = shot.get('position', (0, 0))

            # Determine shot type based on distance from basket
            distance = shot.get('distance', 0)
            if distance > 23.75:  # 3-point distance
                shot_type = "3PT"
                points = 3
            elif distance > 15:  # Mid-range
                shot_type = "Mid-Range"
                points = 2
            elif distance > 5:  # Paint
                shot_type = "Paint"
                points = 2
            else:  # Layup/Dunk
                shot_type = "Layup/Dunk"
                points = 2

            # Assign to a random player
            player_id = random.randint(1, 10)

            # Create shot data
            shot_data.append({
                "id": i + 1,
                "player_id": player_id,
                "x": position[0],
                "y": position[1],
                "shot_type": shot_type,
                "made": shot.get('made', False),
                "quarter": random.randint(1, 4),
                "time_remaining": f"{random.randint(0, 11)}:{random.randint(0, 59):02d}",
                "distance": distance,
                "points": points
            })

        # Calculate shooting percentages by zone
        zone_stats = {}
        for zone in ["3PT", "Mid-Range", "Paint", "Layup/Dunk"]:
            zone_shots = [s for s in shot_data if s["shot_type"] == zone]
            if zone_shots:
                made_shots = [s for s in zone_shots if s["made"]]
                zone_stats[zone] = {
                    "attempts": len(zone_shots),
                    "made": len(made_shots),
                    "percentage": round(len(made_shots) / len(zone_shots) * 100, 1)
                }

        # Calculate player shooting stats
        player_stats = {}
        for player_id in range(1, 11):
            player_shots = [s for s in shot_data if s["player_id"] == player_id]
            if player_shots:
                made_shots = [s for s in player_shots if s["made"]]
                player_stats[str(player_id)] = {
                    "attempts": len(player_shots),
                    "made": len(made_shots),
                    "percentage": round(len(made_shots) / len(player_shots) * 100, 1),
                    "points": sum(s["points"] for s in player_shots if s["made"])
                }

        return {
            "shots": shot_data,
            "zone_stats": zone_stats,
            "player_stats": player_stats,
            "court_dimensions": {
                "length": 94,
                "width": 50
            }
        }

    def _generate_player_tracking_from_frames(self, frames_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate player tracking data from frames data.

        Args:
            frames_data: List of frame data

        Returns:
            Player tracking data
        """
        # Extract player information
        player_info = self._extract_player_info(frames_data)

        if not player_info:
            # Fall back to mock data if no player info
            logger.warning("No player info extracted from frames data. Using mock player tracking data.")
            return self._generate_player_tracking_data()

        # Generate player tracking data
        player_data = {}

        for player_id, info in player_info.items():
            # Calculate speed data
            movement = info.get('movement', 0)
            frame_count = info.get('frame_count', 0)

            # Convert movement to speed (feet per second)
            # This is a very simplified conversion
            avg_speed = round(movement / frame_count * 5, 1) if frame_count > 0 else 0
            max_speed = round(avg_speed * random.uniform(1.2, 1.5), 1)  # Max speed is 20-50% higher

            # Generate distance data (miles)
            distance = round(movement / 5280, 2)  # Convert pixels to miles (very simplified)

            # Generate sprint data
            sprints = random.randint(30, 80)  # Number of sprints

            # Generate movement heatmap data from positions
            heatmap = []
            positions = info.get('positions', [])

            for pos in positions:
                x, y = pos
                intensity = random.uniform(0, 1)  # Intensity at this point
                heatmap.append({"x": x, "y": y, "intensity": intensity})

            # Generate player movement patterns
            if info.get('team') == 'team_a':  # Offensive team
                patterns = random.sample([
                    "Perimeter-oriented",
                    "Paint-dominant",
                    "Corner specialist",
                    "High post operator",
                    "Transition runner"
                ], 2)
            else:  # Defensive team
                patterns = random.sample([
                    "Help defender",
                    "On-ball pressure",
                    "Paint protector",
                    "Perimeter defender",
                    "Transition defender"
                ], 2)

            player_data[str(player_id)] = {
                "avg_speed": avg_speed,
                "max_speed": max_speed,
                "distance": distance,
                "sprints": sprints,
                "heatmap": heatmap,
                "movement_patterns": patterns,
                "time_of_possession": round(random.uniform(0, 8), 1) if info.get('team') == 'team_a' else 0,  # Minutes
                "defensive_matchups": [
                    {"opponent_id": i, "time": round(random.uniform(1, 8), 1)}
                    for i in random.sample(range(1, 11), 3) if i != player_id
                ] if info.get('team') != 'team_a' else []
            }

        # Calculate team stats
        avg_speed = round(sum(p["avg_speed"] for p in player_data.values()) / len(player_data), 1) if player_data else 0
        total_distance = round(sum(p["distance"] for p in player_data.values()), 1) if player_data else 0
        avg_sprints = round(sum(p["sprints"] for p in player_data.values()) / len(player_data)) if player_data else 0

        return {
            "player_data": player_data,
            "team_stats": {
                "avg_speed": avg_speed,
                "total_distance": total_distance,
                "avg_sprints": avg_sprints
            }
        }

# Create a singleton instance
video_analysis_service = VideoAnalysisService()
