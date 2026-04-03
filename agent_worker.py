#!/usr/bin/env python3
"""Agent worker process for LiveKit voice agents."""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path so we can import app modules
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from livekit import agents

from app.agents.voice_agent import server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Starting TalkToYourData agent worker...")

    # Run the agent server
    # This will connect to LiveKit and wait for room assignments
    agents.cli.run_app(server)
