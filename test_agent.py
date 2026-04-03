"""Simple test script to run agent in dev/console mode for debugging."""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Test imports first
try:
    from app.agents.voice_agent import server

    print("✓ Successfully imported voice_agent.server")

    from app.agents.rag_service import rag_service

    print("✓ Successfully imported rag_service")

    from app.db.engine import engine

    print("✓ Successfully imported database engine")

    from livekit.plugins import cartesia

    print("✓ Cartesia plugin available")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)


# Test database connection
async def test_db():
    from sqlmodel import text

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✓ Database connection working")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    print("\n=== Running diagnostic tests ===\n")

    # Test DB
    if not asyncio.run(test_db()):
        print("\n✗ Cannot proceed without database connection")
        sys.exit(1)

    print("\n✓ All tests passed! Agent should work.")
    print("\nNow try running:")
    print("  uv run python agent_worker.py start")
