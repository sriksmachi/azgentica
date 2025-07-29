import os
import json
from pyexpat.errors import messages
from dotenv import load_dotenv
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from image_data_extraction import encode_image
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import BaseMessage
from prompts import data_extraction_prompt, cost_calculation_prompt, json_output_format
from langchain_community.vectorstores import FAISS
import pandas as pd

load_dotenv()

# Set your Azure OpenAI credentials and deployment details
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

# Initialize the AzureChatOpenAI model
llm_client = AzureChatOpenAI(
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version="2024-08-01-preview",
    temperature=0.3,
    model_name=AZURE_OPENAI_DEPLOYMENT_NAME,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

##############################################################################
uploaded_image = None
checkpointer = InMemorySaver()
store = InMemoryStore()

##############################################################################


class ServiceRecommendations(TypedDict):
    service_name: str
    review: str
    recommedation: str
    pillar_in_review: str | None


class Nodes(TypedDict):
    id: str
    type: str
    label: str
    subnet: str | None


class Edges(TypedDict):
    source: str
    target: str
    label: str
    metadata: dict[str, str] | None


class GraphState(TypedDict):
    uploaded_image: str | None
    nodes: list[Nodes] | None
    edges: list[Edges] | None
    image_description: str | None
    azure_services_cost: dict[str, float] | None
    service_recommendations: list[ServiceRecommendations]
    summary: str | None
    total_iterations: int
    pillar_in_review: str | None

###############################################################################


def clean_json_string(json_string):
    """
    Removes '```json' at the beginning and '```' at the end of a string.
    """
    if json_string.startswith("```json"):
        json_string = json_string[len("```json"):].strip()
    if json_string.endswith("```"):
        json_string = json_string[:-len("```")].strip()
    return json_string


def extract_data_from_image(state: GraphState):
    """Extract data from the uploaded image using Azure Document Intelligence."""
    image = state['uploaded_image']
    if not image:
        raise ValueError("No image provided for data extraction.")
    messages = [
        HumanMessage(
            content=[
                {"type": "text", "text": data_extraction_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                            # Use base64 encoded image
                            "url": f"data:image/jpeg;base64,{image}"
                    },
                },
            ]
        )
    ]
    result = llm_client.invoke(messages)
    result_content_json = json.loads(clean_json_string(result.content))
    print(f"Data Extraction Result: {result_content_json}")
    return Command(
        update={
            "uploaded_image": image,
            "image_description": result_content_json["description"],
            "nodes": result_content_json["nodes"],
            "edges": result_content_json["edges"],
        },
        goto="supervisor",
    )


def get_cost_analysis_prompt(state: GraphState):
    """Create a cost analysis prompt."""
    message = [
        SystemMessage(
            content=[
                {"type": "text",
                    "text": cost_calculation_prompt.format(state=state, json_output_format=json_output_format)},
            ]
        )
    ]
    result = llm_client.invoke(message)
    print(f"Cost Analysis Result: {result.content}")
    return Command(
        update={
            "azure_services_cost": json.loads(clean_json_string(result.content))
        },
        goto="supervisor",
    )


###########################
# Create system prompt for supervisor
# Define available agents
members = ["data_extraction", "cost_analysis",
           "service_recommendations_supervisor_node", "summarize_results"]
# Add FINISH as an option for task completion
options = members + ["FINISH"]
system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal["data_extraction", "cost_analysis",
                  "service_recommendations_supervisor_node", "summarize_results", END]


def supervisor_node(state: GraphState):
    messages = [{"role": "system", "content": system_prompt}]
    response = llm_client.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    print(f"Next Worker: {goto}")
    if goto == "FINISH":
        goto = END
    return Command(goto=goto, update={"state": state})


def summarize_results(state: GraphState) -> Command[END]:
    """Summarize the results of the data extraction and cost analysis."""
    messages = [
        SystemMessage(
            content=[
                {
                    "type": "text",
                    "text": f"""Summarize the results of the data extraction and cost analysis. Present the results in a clear and detailed manner as an Architect. \
                    Use the following data to summarize: \
                    - Image Description: {state['image_description']}
                    - Nodes: {state['nodes']}
                    - Edges: {state['edges']}
                    - Azure Services Cost: {state['azure_services_cost']}
                    - Service Recommendations: {state['service_recommendations']}
                    """,
                }
            ]
        )
    ]
    result = llm_client.invoke(messages)
    return Command(
        update={
            "messages": [
                SystemMessage(content=result.content, name="summary_result")
            ]
        },
        goto=END,
    )


####################

def read_csv_file(file_path: str) -> list[dict]:
    """Read a CSV file and return its content as a list of dictionaries."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found at {file_path}")

    df = pd.read_csv(file_path)
    return df.to_dict(orient="records")


def get_service_recommendation_content(service_label: str, service_recommendations_data: list[dict]) -> dict:
    """Get service recommendation content based on the service label. Search for the service label in the service recommendations data."""
    """Note: This could have been a more complex search logic using vector DBs, but for simplicity, we are checking if the service label is present in the heading."""
    for item in service_recommendations_data:
        if service_label.lower() in (item["heading"].lower()):
            return item

        # Check if first 2 words of service label match
        service_label_words = service_label.split()
        if len(service_label_words) >= 2:
            first_two_words = " ".join(service_label_words[:2]).lower()
            last_two_words = " ".join(service_label_words[-2:]).lower()
            for item in service_recommendations_data:
                if item["heading"].lower().startswith(first_two_words):
                    return item
                if item["heading"].lower().endswith(last_two_words):
                    return item
    return None


def service_recommendations_supervisor_node(state: GraphState) -> Command[MessagesState]:
    """Supervisor node for service recommendations workflow."""
    print(f"State for service recommendations {state}")
    nodes = state['nodes']
    generated_service_recommendations = []
    service_recommendations_data = read_csv_file(
        "data/azure-service-recommendations.csv")
    service_recommendations_output_format = """
    [
        {
            "service_name": "Service Name",
            "review": "Review of the service",
            "recommedation": "Recommendation for the service",
            "pillar_in_review": "Pillar in review (Cost, Operational Excellence, Performance Efficiency, Reliability, Security)"
        },
        ...
    ]
    """

    for node in nodes:
        print(f"Processing node: {node}")
        if node['type'] == 'azure':
            service_recommendation = get_service_recommendation_content(
                node['label'], service_recommendations_data)
            if not service_recommendation:
                print(f"No recommendations found for service: {node['label']}")
                continue
            new_message = [
                SystemMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"""You are an Azure Architect, given the architecture diagram and it summary, your task is to review the Azure service: {node['label']} \
                         and provide recommendations based on service recommendations shared by Microsoft as context. The recommendations should be in all 5 pillars of the Azure Well-Architected Framework (WAF): Cost, Operational \
                         Excellence, Performance Efficiency, Reliability, and Security. The recommendations should help improve the Well Architected Score of the architecture. \
                         Context: {service_recommendation},
                         Architecture Summary: {state['image_description']}
                         Output Format: {service_recommendations_output_format}
                        """,
                        }]
                ),
                HumanMessage(
                    content=[
                        {
                            "type": "image_url",
                            "image_url": {
                                # Use base64 encoded image
                                "url": f"data:image/jpeg;base64,{state['uploaded_image']}"
                            },
                        },
                    ])
            ]
            result = llm_client.invoke(new_message)
            result_content_json = json.loads(clean_json_string(result.content))
            print(f"Service Recommendation Result: {result_content_json}")
            generated_service_recommendations.extend(result_content_json)
    return Command(
        update={
            "service_recommendations": generated_service_recommendations,
            "messages": [
                SystemMessage(
                    content=[
                        {"type": "text",
                         "text": "Service recommendations generated successfully."}
                    ]
                )
            ]
        },
        goto="summarize_results"  # Route to summarization node
    )


def document_generator_agent(state: GraphState) -> Command[MessagesState]:
    """Use the content from vector DB to generate response to the ask from user agent."""
    messages = state
    new_message = [
        SystemMessage(
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
                SystemMessage(content=result.content)
            ]
        })


def architecture_reviewer_agent(state: GraphState):
    """Generate a recommendations against each service that is part of the architecture diagram."""
    system_prompt = f"""You are an azure service reviewer agent. Your task is to generate a set of recommendations for each service in the architecture diagram based
    on the Azure Well-Architected Framework(WAF) service recommendations. """
    new_message = [
        SystemMessage(
            content=system_prompt
        )
    ]
    state['messages'] = new_message + state['messages']
    result = llm_client.invoke(state['messages'])
    return Command(
        update={
            "messages": [
                SystemMessage(content=result.content)
            ]
        },
        goto="supervisor"  # Route to evaluator agent for further processing
    )

################################################################################


def graph_builder():
    """Build a sub-graph for the service recommendations workflow."""
    service_recommendations_graph = StateGraph(GraphState)
    service_recommendations_graph.add_node(
        "service_recommendations_supervisor", service_recommendations_supervisor_node)
    service_recommendations_graph.add_node(
        "document_generator", document_generator_agent)
    service_recommendations_graph.add_node(
        "architecture_reviewer", architecture_reviewer_agent)
    service_recommendations_graph.add_edge(
        START, "service_recommendations_supervisor")
    service_recommendations_graph = service_recommendations_graph.compile()

    """Build the state graph for the workflow."""
    graph_builder = StateGraph(GraphState)
    graph_builder.add_node("data_extraction", extract_data_from_image)
    graph_builder.add_node("cost_analysis", get_cost_analysis_prompt)
    graph_builder.add_node("summarize_results", summarize_results)
    graph_builder.add_node("service_recommendations_supervisor_node",
                           service_recommendations_supervisor_node)
    graph_builder.add_edge(START, "data_extraction")
    graph_builder.add_edge("data_extraction", "cost_analysis")
    graph_builder.add_edge(
        "cost_analysis", "service_recommendations_supervisor_node")
    graph_builder.add_edge(
        "service_recommendations_supervisor_node", "summarize_results")
    graph_builder.add_edge("summarize_results", END)
    graph = graph_builder.compile()
    return graph


if __name__ == "__main__":
    # Example usage
    image_path = "azure_architecture_basic.png"
    config = {"configurable": {"thread_id": "1"}}
    encoded_image = encode_image(image_path)
    graph = graph_builder()
    for message in graph.stream(
            {
                "uploaded_image": encoded_image,
            }):
        print(message)
