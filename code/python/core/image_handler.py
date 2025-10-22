import base64
import asyncio
from typing import Dict, Any
from aiohttp import web
import json
import logging

from core.llm import ask_llm
from core.prompts import find_prompt, fill_prompt
from core.config import CONFIG
from misc.logger.logging_config_helper import get_configured_logger

logger = get_configured_logger("image_handler")


class ImageHandler:
    """Handler for processing image uploads and generating sound descriptions."""
    
    def __init__(self):
        self.prompt_name = "GetImageSoundDescription"
        self.site = "image_analysis"
        self.item_type = "Image"
    
    async def process_image(self, image_data: str, query: str = "") -> Dict[str, Any]:
        """Generate sound description from base64 image"""
        try:
            prompt_str, return_struc = find_prompt(self.site, self.item_type, self.prompt_name)
            
            if not prompt_str:
                raise ValueError(f"Prompt '{self.prompt_name}' not found")
            
            class ImagePromptHandler:
                def __init__(self, image_data):
                    self.image_data = image_data
                    self.site = "image_analysis"
                    self.item_type = "Image"
            
            handler = ImagePromptHandler(image_data)
            
            filled_prompt = fill_prompt(prompt_str, handler)
            
            logger.info(f"Processing image with Gemini for sound description")
            
            response = await ask_llm(
                prompt=filled_prompt,
                schema=return_struc,
                provider="gemini",
                level="high",
                image_data=image_data
            )
            
            if response and "sound_description" in response:
                return {
                    "success": True,
                    "sound_description": response["sound_description"],
                    "prompt_used": self.prompt_name
                }
            else:
                return {
                    "success": False,
                    "error": "No sound description generated",
                    "response": response
                }
                
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


async def handle_image_upload(request: web.Request) -> web.Response:
    """POST /api/image/analyze."""
    try:
        data = await request.json()
        
        if "image" not in data:
            return web.json_response({
                "success": False,
                "error": "No image data provided"
            }, status=400)
        
        image_data = data["image"]
        query = data.get("query", "")
        
        try:
            base64.b64decode(image_data)
        except Exception:
            return web.json_response({
                "success": False,
                "error": "Invalid base64 image data"
            }, status=400)
        
        handler = ImageHandler()
        result = await handler.process_image(image_data, query)
        
        return web.json_response(result)
        
    except json.JSONDecodeError:
        return web.json_response({
            "success": False,
            "error": "Invalid JSON request"
        }, status=400)
    except Exception as e:
        logger.error(f"Error in handle_image_upload: {str(e)}")
        return web.json_response({
            "success": False,
            "error": "Internal server error"
        }, status=500)


async def handle_audio_generation(request: web.Request) -> web.Response:
    """POST /api/audio/generate."""
    try:
        data = await request.json()
        
        if "sound_description" not in data:
            return web.json_response({
                "success": False,
                "error": "No sound description provided"
            }, status=400)
        
        sound_description = data["sound_description"]
        
        from core.audioldm_handler import audio_handler
        result = await audio_handler.process_sound_description(sound_description)
        
        return web.json_response(result)
        
    except json.JSONDecodeError:
        return web.json_response({
            "success": False,
            "error": "Invalid JSON request"
        }, status=400)
    except Exception as e:
        logger.error(f"Error in handle_audio_generation: {str(e)}")
        return web.json_response({
            "success": False,
            "error": "Internal server error"
        }, status=500)


def setup_image_routes(app: web.Application):
    """Setup image handling routes above"""
    app.router.add_post('/api/image/analyze', handle_image_upload)
    app.router.add_post('/api/audio/generate', handle_audio_generation)
    logger.info("Image handler routes configured")
