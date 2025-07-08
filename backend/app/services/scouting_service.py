"""
Scouting Service Client - Communicates with the scouting service
"""
import httpx
import asyncio
from typing import Dict, Optional, List
from app.core.config import settings

class ScoutingServiceClient:
    """Client for communicating with the scouting service"""
    
    def __init__(self):
        self.base_url = settings.SCOUTING_SERVICE_URL
        self.timeout = 30.0
    
    async def start_analysis(self, video_id: int, video_path: str, analysis_options: Optional[Dict] = None) -> Dict:
        """
        Start video analysis job
        
        Args:
            video_id: ID of the video in the main database
            video_path: Path to the video file in MinIO
            analysis_options: Optional analysis configuration
            
        Returns:
            Dict with job_id and status
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/analyze",
                    params={
                        "video_id": video_id,
                        "video_path": video_path
                    },
                    json=analysis_options or {}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to scouting service: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Scouting service error: {e.response.status_code} - {e.response.text}")
    
    async def get_job_status(self, job_id: str) -> Dict:
        """
        Get analysis job status
        
        Args:
            job_id: Analysis job ID
            
        Returns:
            Dict with job status information
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/jobs/{job_id}/status")
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to scouting service: {str(e)}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise Exception(f"Scouting service error: {e.response.status_code} - {e.response.text}")
    
    async def get_result_url(self, job_id: str) -> Optional[str]:
        """
        Get analysis result download URL
        
        Args:
            job_id: Analysis job ID
            
        Returns:
            URL to download the analysis result or None if not available
        """
        try:
            # Return the direct URL to the result endpoint
            return f"{self.base_url}/api/jobs/{job_id}/result"
            
        except Exception as e:
            print(f"Error generating result URL: {str(e)}")
            return None
    
    async def list_jobs(self) -> List[Dict]:
        """
        List all analysis jobs
        
        Returns:
            List of job status dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/jobs")
                response.raise_for_status()
                return response.json()
                
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to scouting service: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Scouting service error: {e.response.status_code} - {e.response.text}")
    
    async def delete_job(self, job_id: str) -> bool:
        """
        Delete analysis job and results
        
        Args:
            job_id: Analysis job ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(f"{self.base_url}/api/jobs/{job_id}")
                response.raise_for_status()
                return True
                
        except httpx.RequestError as e:
            print(f"Failed to connect to scouting service: {str(e)}")
            return False
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            print(f"Scouting service error: {e.response.status_code} - {e.response.text}")
            return False
    
    async def health_check(self) -> bool:
        """
        Check if scouting service is healthy
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
                
        except Exception:
            return False

# Create singleton instance
scouting_service_client = ScoutingServiceClient()
