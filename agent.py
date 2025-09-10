from dotenv import load_dotenv
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool
from livekit.plugins import (
    google,
    noise_cancellation,
)
from mcp_client import MCPServerSse
from mcp_client.agent_tools import MCPToolsIntegration
import os
from tools import open_url
from kb import get_kb_answer
from livekit.plugins import tavus
from livekit.plugins import bey
load_dotenv()


@function_tool
async def answer_hotel_question(question: str) -> str:
    """
    Answer questions about Grand Luxe Hotel by referencing the knowledge base.
    
    Args:
        question: A question about the hotel's services, amenities, policies, or information.
        
    Returns:
        A relevant answer based on the hotel's knowledge base.
    """
    try:
        answer = get_kb_answer(question)
        return answer
    except Exception as e:
        return f"I'm having trouble accessing the hotel information right now. Please try again later."


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=AGENT_INSTRUCTION,
                         tools=[open_url, answer_hotel_question],)


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Aoede",  # Female voice
        ),
    )

    mcp_server = MCPServerSse(
        params={"url": os.environ.get("N8N_MCP_SERVER_URL")},
        cache_tools_list=True,
        name="SSE MCP Server"
    )

    agent = await MCPToolsIntegration.create_agent_with_tools(
        agent_class=Assistant,
        mcp_servers=[mcp_server]
    )
    # avatar = bey.AvatarSession(
    #     avatar_id=os.environ.get("BEY_AVATAR_ID"),
    #     api_key=os.environ.get("BEY_API_KEY"),
    # )

    # avatar = tavus.AvatarSession(
    #     replica_id=os.environ.get("REPLICA_ID"),  
    #     persona_id=os.environ.get("PERSONA_ID"),  
    #     api_key=os.environ.get("TAVUS_API_KEY"),
    # )

    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))