import requests
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from misc.logger.logging_config_helper import get_configured_logger

logger = get_configured_logger("audioldm_handler")

# Google Colab public URL running in ngrok
PUBLIC_URL = "https://tristen-symbolistic-crystal.ngrok-free.dev"  

# Google colab API key
API_KEY = "multimedia-482jf2l4512"  


class AudioLDMHandler:
    """Generate audio from text descriptions."""
    
    def __init__(self):
        self.headers = {"x-api-key": API_KEY}
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.output_dir = project_root / "static" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Audio output directory: {self.output_dir.resolve()}")
    
    async def process_sound_description(self, sound_description: str) -> Dict[str, Any]:
        """Call /generate, download WAV, return web URL."""
        try:
            logger.info(f"Generating audio for description: {sound_description[:100]}...")
            
            req = {
                "prompt": sound_description,
                "seconds": 10.0,
                "steps": 200,
                "guidance": 3.2,
                "seed": None
            }
            
            r = requests.post(
                f"{PUBLIC_URL}/generate",
                json=req,
                headers=self.headers,
                timeout=600
            )
            r.raise_for_status()
            meta = r.json()
            
            logger.info(f"Audio generation meta: {json.dumps(meta, indent=2)}")
            
            if "download_url" in meta:
                download_url = meta["download_url"]
            elif "filename" in meta:
                download_url = f"{PUBLIC_URL}/download/{meta['filename']}"
            else:
                raise ValueError("Response missing 'download_url' or 'filename'")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{timestamp}.wav"
            wav_path = self.output_dir / filename
            
            logger.info(f"Downloading audio from: {download_url}")
            
            with requests.get(download_url, headers=self.headers, stream=True) as resp:
                resp.raise_for_status()
                with open(wav_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            logger.info(f"Audio saved: {wav_path.resolve()}")
            
            return {
                "success": True,
                "audio_url": f"/static/audio/{filename}"
            }
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
audio_handler = AudioLDMHandler()
