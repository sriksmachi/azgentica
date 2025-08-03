import base64
import streamlit as st
from workflow import AzureArchitectureWorkflow
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

st.title("🦜🔗 Azgentica")
st.markdown(
    "An AI-powered tool to analyze Azure architecture diagrams and extract key components and relationships."
)


################################################################################
submitted = False
with st.sidebar:
    st.markdown("### About")
    st.markdown(
        "Azgentica is an AI-powered tool that helps you analyze Azure architecture diagrams and extract key components and relationships. \
            It uses advanced language models to interpret the diagram and provide insights in a structured format."
    )
    st.markdown("### Instructions")
    st.markdown(
        "1. Upload an image of an Azure architecture diagram.\n"
        "2. Click on 'Generate Summary' to analyze the diagram.\n"
        "3. The tool will extract key components, their relationships, and provide a summary in JSON format.\n"
        "4. The results will be displayed below the upload section.\n"
    )
    with st.form("chat_form"):

        # Image upload section
        st.header("Upload an Image", anchor="upload-image",
                  help="Upload an Azure architecture diagram image to analyze.")

        uploaded_image = st.file_uploader(
            "Choose an image...", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Generate Summary")

if uploaded_image:
    st.image(uploaded_image, caption="Uploaded Image",
             use_container_width=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if submitted and uploaded_image:
    encoded_image = base64.b64encode(
        uploaded_image.getvalue()).decode("utf-8")
    workflow = AzureArchitectureWorkflow()
    graph = workflow.graph_builder()
    with st.status("Processing..."):
        for chunk in graph.stream(
                {
                    "uploaded_image": encoded_image,
                }, stream_mode=["values"]):
            values = chunk[1]
            if "messages" in values.keys() and values["messages"]:
                st.status(values["messages"][-1].content[0]
                          ["text"], state="complete")
        st.status(
            "Processing completed. Displaying results...", state="complete")
        # Use the last chunk to display the summary
    last_chunk_values = chunk[1]
    if "summary" in last_chunk_values.keys() and last_chunk_values["summary"]:
        st.markdown(last_chunk_values["summary"])
