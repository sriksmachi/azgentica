import base64
import streamlit as st
from workflow import graph_builder
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

st.title("🦜🔗 Azgentica")
st.markdown(
    "This app allows you to upload an Azure architecture diagram image and interact with a language model to extract information from it."
)


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
    uploaded_image = st.file_uploader(
        "Choose an image...", type=["jpg", "jpeg", "png"])

# Image upload section
st.header("Upload an Image", anchor="upload-image",
          help="Upload an Azure architecture diagram image to analyze.")

if uploaded_image:
    st.image(uploaded_image, caption="Uploaded Image",
             use_container_width=True)

# Chat interface section
st.header("Chat with the agent", anchor="chat-interface",
          help="Type your questions or prompts related to the uploaded image.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def generate_response(input_text, uploaded_image):
    """Generate a response from the model based on user input and uploaded image."""
    workflow = graph_builder()
    if not uploaded_image:
        st.error("Please upload an image before sending a message.")
        return "No image uploaded."
    # convert byte array to base64 string
    encoded_image = base64.b64encode(uploaded_image.getvalue()).decode("utf-8")
    st_callback = StreamlitCallbackHandler(st.container())
    return workflow.stream({"uploaded_image": encoded_image}, {"callbacks": [st_callback]})


with st.form("chat_form"):
    user_input = st.text_area("Your message:", "")
    submitted = st.form_submit_button("Send")
    if submitted and user_input and uploaded_image:
        response = generate_response(user_input, uploaded_image)
        # Display the response
        for chunk in response:
            st.write(chunk["output"])
