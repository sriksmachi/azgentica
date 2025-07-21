import os
import base64
import uuid
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from IPython.display import Markdown
from langchain_core.output_parsers import JsonOutputParser

# Load environment variables from .env file for secure credential management
load_dotenv()

# Retrieve Azure and OpenAI configuration from environment variables
chat_model = os.getenv("AOAI_CHAT_DEPLOYMENT_NAME", "gpt-4o")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")

# Initialize Azure OpenAI chat client for LLM-based summarization
llm_client = AzureChatOpenAI(
    azure_deployment=chat_model,
    api_version="2023-05-15",
    temperature=0.3,
    model_name=chat_model,
    azure_endpoint=aoai_endpoint,
    api_key=aoai_key,
)


# Text Summarization
data_extraction_prompt = """You are a vision-language model specialized in reading architecture diagrams.

Given an Azure architecture diagram image:
1. **Identify all services and components** used in the diagram.
   - Treat each service/component as a **node**.
   - For Azure-native components (e.g., App Service, Key Vault), use their standard names.
   - For custom or third-party components, extract their labels from the image.
   - Include special infrastructure blocks such as firewalls, DNS, build agents, bastion hosts, and monitoring tools.
   - Capture zones or subnets if shown.

2. **Determine the interconnectivity** between components.
   - Each connection (e.g., arrow, line, pipeline) should become a **directed edge** between two nodes.
   - Respect the direction and label of the connection (e.g., HTTP request, private endpoint, secured access).
   - If labels or text are associated with the edges, extract and include them.

3. **Output the extracted data** in the following JSON format:
```json
{
  "nodes": [
    {"id": "App Service", "type": "azure", "label": "Azure App Service"},
    {"id": "OpenAI", "type": "azure", "label": "Azure OpenAI Service"},
    {"id": "Custom Agent", "type": "custom", "label": "Foundry Agent Service"},
    ...
  ],
  "edges": [
    {"source": "App Service", "target": "OpenAI", "label": "calls OpenAI endpoint"},
    {"source": "User", "target": "App Service", "label": "HTTP request via App Gateway"},
    ...
  ]
}

4. **Additional Guidelines**
- If any element is visually grouped or placed within a subnet, add that relationship as metadata. 
- Perform OCR for custom components or blocks with text. 
- Add `"subnet"` or `"zone"` as an optional field in nodes. 
- Use `"metadata"` field in edges to include optional notes like protocol (HTTPS, REST, etc.)
"""
prompt = ChatPromptTemplate.from_template(data_extraction_prompt)

# Function to encode image to base64 string


def encode_image(image_path):
    '''Getting the base64 string'''
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# Function to summarize an image using the LLM client
def image_analysis(image_path):
    """Make image summary"""
    img_base64 = encode_image(image_path)
    parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("human", data_extraction_prompt),
            ("image", {"type": "image_url", "image_url": {
             "url": f"data:image/jpeg;base64,{img_base64}"}})
        ]
    )
    result = prompt | llm_client | parser
    msg = result.invoke([HumanMessage(content="Analyze this image")])
    response = msg.content.replace("```json\n", "").replace("\n```", "")
    return response
