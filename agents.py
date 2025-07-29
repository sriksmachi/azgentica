import os
import json
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langchain_community.chat_models import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command
from pyexpat.errors import messages
from dotenv import load_dotenv
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from prompts import data_extraction_prompt, cost_calculation_prompt
from langchain_core.messages import HumanMessage
from image_data_extraction import encode_image
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from image_data_extraction import create_prompt_with_image
from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import MessagesState, START, END
from langgraph.types import Command


# Set up environment variables
def document_generator_agent(state: MessagesState) -> Command[MessagesState]:
    """Use the content from vector DB to generate response to the ask from user agent."""
    messages = state['messages'][0]
    new_message = [
        HumanMessage(
            content=[
                {"type": "text",
                 "text": "Based on the PDF content, prepare a questionnare and a check list that can be used by \
                     a architecture reviewer agent to review an architecture"},
            ]
        )

    ]
    result = llm_client.invoke(messages + new_message)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result.content)
            ]
        })
