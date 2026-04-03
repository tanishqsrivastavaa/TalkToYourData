"""LiveKit Voice Agent with RAG integration."""

import logging
import os
import uuid

from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
    ChatMessage,
    JobContext,
)
from livekit.plugins import openai, silero
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.agents.rag_service import rag_service
from app.core.config import settings
from app.db.engine import engine

logger = logging.getLogger(__name__)

# Import cartesia if available, otherwise use OpenAI TTS fallback
try:
    from livekit.plugins import cartesia

    CARTESIA_AVAILABLE = True
except ImportError:
    CARTESIA_AVAILABLE = False
    logger.warning("Cartesia plugin not available, will use OpenAI TTS instead")

# Agent server instance
server = AgentServer()


class VoiceAssistant(Agent):
    """Voice assistant with RAG capabilities."""

    def __init__(self, user_id: uuid.UUID, chat_ctx: ChatContext | None = None):
        """
        Initialize the voice assistant.

        Args:
            user_id: The ID of the user for scoping document searches
            chat_ctx: Optional initial chat context
        """
        super().__init__(
            chat_ctx=chat_ctx,
            instructions="""You are a helpful voice AI assistant for TalkToYourData.

Your primary role is to help users get information from their uploaded documents.
When users ask questions, you will receive relevant excerpts from their documents 
to help you provide accurate, contextual answers.

Guidelines:
- Be conversational and friendly
- Keep responses concise and natural for voice interaction
- If you receive document context, cite the source document when helpful
- If no relevant documents are found, let the user know and offer to help with general questions
- Speak clearly and avoid complex formatting, symbols, or emojis
""",
        )
        self.user_id = user_id

    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage
    ) -> None:
        """
        Hook called after user completes their turn.
        Performs RAG retrieval and injects context before LLM generation.
        """
        user_query = new_message.text_content()
        logger.info(f"User query: {user_query}")

        # Create database session
        async with SQLModelAsyncSession(engine) as session:
            try:
                # Perform RAG retrieval
                context, num_chunks = await rag_service.retrieve_context(
                    session=session,
                    user_id=self.user_id,
                    query=user_query,
                    top_k=3,
                    similarity_threshold=0.7,
                )

                if context:
                    logger.info(f"Found {num_chunks} relevant chunks")
                    # Inject retrieved context into the conversation
                    turn_ctx.add_message(
                        role="system",
                        content=f"""RELEVANT DOCUMENT EXCERPTS:

{context}

Use the above information to answer the user's question accurately. 
If the information helps answer their question, mention which document it came from.
If the excerpts don't contain relevant information, let the user know.""",
                    )
                else:
                    logger.info("No relevant documents found")
                    # Let the LLM know no documents were found
                    turn_ctx.add_message(
                        role="system",
                        content="No relevant documents were found in the user's uploaded files for this query. Let them know you couldn't find relevant information in their documents, and offer to help with general questions.",
                    )

            except Exception as e:
                logger.error(f"Error during RAG retrieval: {e}", exc_info=True)
                # On error, add a system message but don't fail
                turn_ctx.add_message(
                    role="system",
                    content="There was an issue searching the documents. Continue the conversation normally.",
                )


@server.rtc_session(agent_name="talktoyourdata-agent")
async def voice_agent_entrypoint(ctx: JobContext):
    """
    Agent entrypoint called when a new room is created.
    Sets up the voice agent with STT, LLM, TTS, and RAG.
    """
    logger.info(f"Starting agent for room: {ctx.room.name}")

    # Extract user_id from room metadata or participant attributes
    # For now, we'll use the first participant's identity as user_id
    # In production, you'd pass this via room metadata or participant attributes
    await ctx.connect()

    # Wait for a participant to join
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # In a real implementation, you'd extract the user_id from:
    # 1. Room metadata (set when creating the room)
    # 2. Participant attributes (set when generating the token)
    # For now, we'll try to parse it from identity or use a placeholder
    try:
        user_id = uuid.UUID(participant.identity)
    except ValueError:
        # If identity is not a UUID, try to get from attributes
        user_id_str = participant.attributes.get("user_id")
        if user_id_str:
            user_id = uuid.UUID(user_id_str)
        else:
            logger.warning(
                f"Could not extract user_id from participant {participant.identity}"
            )
            # For demo purposes, we'll continue but RAG will fail
            # In production, you should fail here or use a default
            user_id = uuid.uuid4()

    # Select TTS provider based on availability
    if CARTESIA_AVAILABLE and settings.cartesia_api_key:
        tts_provider = cartesia.TTS(
            api_key=settings.cartesia_api_key,
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",  # Sonic 3 voice
        )
        logger.info("Using Cartesia TTS")
    else:
        tts_provider = openai.TTS(
            model="tts-1",
            voice="alloy",
            api_key=settings.openai_api_key,
        )
        logger.info("Using OpenAI TTS (Cartesia not available)")

    # Create agent session with STT-LLM-TTS pipeline
    session = AgentSession(
        stt=openai.STT(
            model="whisper-1",
            api_key=settings.openai_api_key,
        ),
        llm=openai.LLM(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
        ),
        tts=tts_provider,
        vad=silero.VAD.load(),
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(user_id=user_id),
    )

    # Generate initial greeting
    await session.generate_reply(
        instructions="""Greet the user warmly and let them know you can help them 
find information in their uploaded documents. Keep it brief and natural."""
    )

    logger.info("Agent session started successfully")
