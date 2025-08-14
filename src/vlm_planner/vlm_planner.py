
# vlm_planner.py

import google.generativeai as genai
import os
import time
import json

from PIL import Image
import typing_extensions as typing
from prompt import create_trajectory_prompt

class TrajectoryPoint3D(typing.TypedDict):
    """3D coordinate information of TrajectoryPoint passed to Gemini"""
    x: float
    y: float
    z: float
    time: float
    velocity: float

class TrajectoryResponse(typing.TypedDict):
    """Response schema passed to Gemini"""
    current_sector: int
    trajectory_points: list[TrajectoryPoint3D]
    reasoning: str
    command: str

class VLMPlanner:
    """
    Class for image recognition and trajectory generation using VLM
    """
    def __init__(self, logger):
        self.logger = logger
        self.model = None
        self.last_commands = ["go straight"]  # History of commands inferred by VLM
        self.current_sector = 1  # Current sector managed internally
        self._setup_gemini()

    def _setup_gemini(self):
        """
        Set up the Gemini model.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.logger.error("Environment variable 'GEMINI_API_KEY' is not set.")
            raise ValueError("API key is missing.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
        self.logger.info("VLMPlanner: Gemini model initialized successfully.")

    def _preprocess_image(self, image: Image) -> Image:
        """
        Crop and resize the image.
        """
        pil_image = image.copy()
        # Adjust recognition area
        w, h = pil_image.size
        crop_box = (0, h // 2 - 200, w, h // 2 + 200)
        pil_image = pil_image.crop(crop_box)
        pil_image = pil_image.resize((w // 4, (crop_box[3] - crop_box[1]) // 4))
        return pil_image

    def generate_trajectory(self, image: Image, last_trajectory_action: str, current_velocity: float, current_position: tuple) -> list:
        """
        Generate a trajectory using VLM based on the given image.
        """
        if self.model is None:
            self.logger.warn("VLM model is not ready.")
            return []

        processed_image = self._preprocess_image(image)
        
        prompt = create_trajectory_prompt(last_trajectory_action, self.current_sector, current_velocity, current_position, self.last_commands)
        
        try:
            start = time.perf_counter()
            response = self.model.generate_content(
                [prompt, processed_image],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=TrajectoryResponse,
                    temperature=0.0,
                ),
            )
            end = time.perf_counter()
            latency = end - start
            self.logger.info(f"Gemini trajectory generation latency: {latency:.4f}s")
            self.logger.info(f"Response: {response.text.strip()}")
            response_dict = json.loads(response.text.strip())
            trajectory_points = response_dict.get("trajectory_points", [])
            self.current_sector = response_dict.get("current_sector", self.current_sector)
            reasoning = response_dict.get("reasoning", "")
            command = response_dict.get("command", "go straight")
            self.last_commands.append(command)

            self.logger.info(f"Generated {len(trajectory_points)} points. sector: {self.current_sector}")
            self.logger.info(f"Reasoning: {reasoning}")
            self.logger.info(f"Command: {command}")

            return trajectory_points
                
        except Exception as e:
            self.logger.error(f"Error during VLM trajectory generation: {e}")
            return []
