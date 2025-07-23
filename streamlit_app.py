from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph_supervisor import create_supervisor
from langchain_core.messages import convert_to_messages, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from typing_extensions import TypedDict
from prompts import data_extraction_prompt, cost_calculation_prompt, json_output_format
import streamlit as st
import os
from langchain.chat_models import AzureChatOpenAI
from dotenv import load_dotenv
from image_data_extraction import create_prompt_with_image

load_dotenv()


st.title("🦜🔗 Azgentica")
st.markdown(
    "This app allows you to upload an Azure architecture diagram image and interact with a language model to extract information from it."
)

# Set your Azure OpenAI credentials and deployment details
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Initialize the AzureChatOpenAI model
llm_client = AzureChatOpenAI(
    openai_api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version="2023-05-15"
)

##############################################################################
uploaded_image = None
checkpointer = InMemorySaver()
store = InMemoryStore()

data_gatherer_agent = create_react_agent(
    model=llm_client,
    tools=[],
    prompt=create_prompt_with_image(
        uploaded_image, data_extraction_prompt),
    name="data_gatherer_agent",
)

cost_analysis_agent = create_react_agent(
    model=llm_client,
    tools=[],
    prompt=cost_calculation_prompt,
    name="cost_analysis_agent",
)

workflow = create_supervisor(
    model=llm_client,
    agents=[data_gatherer_agent, cost_analysis_agent],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a data extraction agent. Assign data extraction tasks to this agent\n"
        "- a cost analysis agent. Assign cost analysis related tasks to this agent \n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),

).compile(checkpointer=checkpointer, store=store)


################################################################################


with st.sidebar:
    st.markdown("### About")
    st.markdown(
        "This Streamlit app lets you upload an architecture diagram image and interact with a language model to extract information from it. "
    )
    st.markdown("### Instructions")
    st.markdown(
        "1. Upload an image of an Azure architecture diagram.\n"
        "2. Type your questions or prompts in the chat box.\n"
        "3. The model will analyze the image and respond based on the content of the diagram."
    )

# Image upload section
st.header("Upload an Image")
uploaded_image = st.file_uploader(
    "Choose an image...", type=["jpg", "jpeg", "png"])
if uploaded_image:
    st.image(uploaded_image, caption="Uploaded Image",
             use_container_width=True)

# Chat interface section
st.header("Chat with the Model")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def generate_response(input_text):
    return workflow.invoke(input_text, store=st.session_state.store).get("output", "No response generated.")


with st.form("chat_form"):
    user_input = st.text_area("Your message:", "")
    submitted = st.form_submit_button("Send")
    if submitted and user_input:
        response = generate_response(user_input)
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Assistant", response))

# Display chat history
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f"**You:** {message}")
    else:
        st.markdown(f"**Assistant:** {message}")
