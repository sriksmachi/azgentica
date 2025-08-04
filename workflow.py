import base64
import os
import json
import time
import logging
import pandas as pd
import click
from dotenv import load_dotenv
from typing import Literal
from typing_extensions import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_openai import AzureChatOpenAI
from langchain_ollama import ChatOllama

from prompts import data_extraction_prompt, cost_calculation_prompt, json_output_format

from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)


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
    messages: list[BaseMessage] | None


class Router(TypedDict):
    next: Literal["data_extraction", "cost_analysis",
                  "service_recommendations_supervisor_node", "summarize_results", END]


class AzureArchitectureWorkflow:
    def __init__(self):
        self.AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        self.AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv(
            "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        self.llm_client = AzureChatOpenAI(
            azure_deployment=self.AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version="2024-08-01-preview",
            temperature=0.3,
            model_name=self.AZURE_OPENAI_DEPLOYMENT_NAME,
            azure_endpoint=self.AZURE_OPENAI_ENDPOINT,
            api_key=self.AZURE_OPENAI_API_KEY,
        )
        self.members = [
            "data_extraction",
            "cost_analysis",
            "service_recommendations_supervisor_node",
            "summarize_results"
        ]
        self.options = self.members + ["FINISH"]

    @staticmethod
    def encode_image(image_path):
        '''Getting the base64 string'''
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @staticmethod
    def clean_json_string(json_string):
        if json_string.startswith("```json"):
            json_string = json_string[len("```json"):].strip()
        if json_string.endswith("```"):
            json_string = json_string[:-len("```")].strip()
        return json_string

    @staticmethod
    def read_csv_file(file_path: str) -> list[dict]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found at {file_path}")
        df = pd.read_csv(file_path)
        return df

    @staticmethod
    def get_service_recommendation_content(df, service_label: str, min_common_words=2):
        target_words = set(service_label.lower().split())
        results = None
        for _, row in df.iterrows():
            source_words = set(str(row['heading']).lower().split())
            common = target_words & source_words
            if len(common) >= min_common_words:
                results = row["content"]
                break
        return results

    def extract_data_from_image(self, state: GraphState):
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
                            "url": f"data:image/jpeg;base64,{image}"
                        },
                    },
                ]
            )
        ]
        result = self.llm_client.invoke(messages)
        result_content_json = json.loads(
            self.clean_json_string(result.content))
        return Command(
            update={
                "uploaded_image": image,
                "image_description": result_content_json["description"],
                "nodes": result_content_json["nodes"],
                "edges": result_content_json["edges"],
                "summary": result_content_json["description"],
                "messages": [
                    SystemMessage(
                        content=[
                            {"type": "text",
                             "text": f"Extracted data from image, transferring to cost analysis node."},
                        ]
                    )]
            },
            goto="cost_analysis",
        )

    def get_cost_analysis_prompt(self, state: GraphState):
        message = [
            SystemMessage(
                content=[
                    {"type": "text",
                     "text": cost_calculation_prompt.format(state=state, json_output_format=json_output_format)},
                ]
            )
        ]
        result = self.llm_client.invoke(message)
        return Command(
            update={
                "azure_services_cost": json.loads(self.clean_json_string(result.content)),
                "messages": [
                    SystemMessage(
                        content=[
                            {"type": "text",
                             "text": f"Cost analysis completed, generating service recommendations."},
                        ]
                    )]
            },
            goto="service_recommendations_supervisor_node",
        )

    def service_recommendations_supervisor_node(self, state: GraphState) -> Command:
        nodes = state['nodes']
        generated_service_recommendations = []
        csv_path = "data/azure-service-recommendations.csv"
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"CSV file not found at {csv_path}, Run the datapipeline.py to generate the CSV file.")
        service_recommendations_data = self.read_csv_file(csv_path)
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
            if node['type'] == 'azure':
                service_recommendation = self.get_service_recommendation_content(service_recommendations_data,
                                                                                 node['label'])
                if not service_recommendation:
                    logger.warning(
                        f"No recommendations found for service: {node['label']}")
                    continue
                new_message = [
                    SystemMessage(
                        content=[
                            {
                                "type": "text",
                                "text": f"""You are an Azure Architect, given the architecture diagram and it summary, your task is to review the Azure service: {node['label']} \
                             and provide recommendations based on service recommendations shared by Microsoft as context. The recommendations should be in all 5 pillars of the Azure Well-Architected Framework (WAF): Cost, Operational \
                             Excellence, Performance Efficiency, Reliability, and Security. The recommendations should help improve the Well Architected Score of the architecture. \
                             ### Context: {service_recommendation},
                             ### Architecture Summary: {state['image_description']}
                             ### Output Format: {service_recommendations_output_format}
                            """,
                            }]
                    ),
                    HumanMessage(
                        content=[
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{state['uploaded_image']}"
                                },
                            },
                        ])
                ]
                result = self.llm_client.invoke(new_message)
                result_content_json = json.loads(
                    self.clean_json_string(result.content))
                generated_service_recommendations.extend(result_content_json)
            else:
                logger.warning(
                    f"Node {node['label']} is not an Azure service, skipping service recommendations generation.")
        return Command(
            update={
                "service_recommendations": generated_service_recommendations,
                "messages": [
                    SystemMessage(
                        content=[
                            {"type": "text",
                             "text": f"Service recommendations generated, transferring to summarization node."},
                        ]
                    )]
            },
            goto="summarize_results"
        )

    def summarize_results(self, state: GraphState):
        messages = [
            SystemMessage(
                content=[
                    {
                        "type": "text",
                        "text": f"""

                        Summarize the results of the data extraction and cost analysis.  \
                        Present the results in a clear and detailed manner as an Architect. \
                        Use the following data to summarize: \

                        ## State Description and Data:
                        - **Image Description**: Description of the architecture diagram. **Data** - {state['image_description']}
                        - **Nodes**: Azure services and their details. **Data** - {state['nodes']}
                        - **Edges**: Connections between the services. **Data** - {state['edges']}
                        - **Azure Services Cost**: Cost of each Azure service used in the architecture. **Data** - {state['azure_services_cost']}
                        - **Service Recommendations**: Recommendations for each service based on the Azure Well-Architected Framework. Each recommendation should include:
                            - **Service Name**: Name of the Azure service.
                            - **Review**: Review of the service.
                            - **Recommendation**: Recommendation for the service.
                            - **Pillar in Review**: Pillar in review (Cost, Operational Excellence, Performance Efficiency, Reliability, Security).
                            - **Data** - {state['service_recommendations']}
                        - **Summary**: Summary of the architecture diagram including the image description, architecture description, services used, cost analysis, and service recommendations.
                           

                        ## Instructions:
                        - Provide a comprehensive summary of the architecture diagram, including the image description, architecture description, services used, cost analysis, and service recommendations.
                        - Remember the data could be empty in few areas in the state, so handle it gracefully.
                        - Only use the data provided in the state to summarize. Do not make assumptions or add any additional information from your knowledge.

                        ## Formatting instructions:
                        - Use markdown format for the summary.
                        - Use headings to separate different sections of the summary.
                        - Use bullet points for lists.
                        - Convert Service Recommendations to a structured table format.
                        - Convert Azure Services Cost to a structured table format.
                        - Convert Nodes as list of dictionaries.

                        ## Format of the summary should be in markdown format as follows:

                        ## **Architecture Summary**
                        - **Summary**:  As an Azure Architect, summarize the architecture diagram based on the data provided in the state. List its objectives, purpose, limitations and key risks. \
                        - **Services Used**: <<List of services used in the architecture diagram and its purpose, should be in table format>>
                        ### **Cost Analysis**
                        - **Summary of Azure Services Cost**: Create a summary of Azure services cost, total cost per month, and cost breakdown by service. \
                        - **Total Cost**: <<Total cost of the architecture diagram>>
                        - **Azure Compute Services Cost**: <<Data should be in text format>>
                        - **Azure Storage Services Cost**: <<Data should be in text format>>
                        - **Azure Networking Services Cost**: <<Data should be in text format>>
                        
                        ## **Azure Services Cost**:  
                        <<Data should be in table format>>
                        
                        ### **Service Recommendations**
                        - **Recommendations**: <<Data should be in table format>>
                        ### **Nodes**
                        - **Nodes**: <<Data should be in list of dictionaries format>>
                        ### **Edges**
                        - **Edges**: <<Data should be in list of dictionaries format>>
                        """,
                    }
                ]
            )
        ]
        try:
            result = self.llm_client.invoke(messages)
            return Command(
                update={
                    "summary": result.content,
                    "messages": [
                        SystemMessage(
                            content=[
                                {"type": "text",
                                 "text": f"Summarization completed, transferring to {END}."},
                            ]
                        )]
                },
                goto=END
            )
        except Exception as e:
            logging.error(f"Error during summarization: {e}")
            return Command(
                update={
                    "summary": "Error during summarization: " + str(e),
                    "messages": [
                        SystemMessage(
                            content=[
                                {"type": "text",
                                 "text": f"Error during summarization: {e}, go to {END}."},
                            ]
                        )]
                },
                goto=END
            )

    def graph_builder(self):
        graph_builder = StateGraph(GraphState)
        graph_builder.add_node("data_extraction", self.extract_data_from_image)
        graph_builder.add_node("cost_analysis", self.get_cost_analysis_prompt)
        graph_builder.add_node("service_recommendations_supervisor_node",
                               self.service_recommendations_supervisor_node)
        graph_builder.add_node("summarize_results", self.summarize_results)
        graph_builder.add_edge(START, "data_extraction")
        graph = graph_builder.compile()
        return graph


@click.command()
@click.option(
    "--image_path", "-i",
    default="sample_images/azure_architecture_basic.png",
    show_default=True,
    help="Path to the input image file."
)
@click.option('--output', '-o', default=None, help="Output file for the summary. Defaults to 'summary<timestamp>.md'.")
def analyze(image_path, output):
    """
    Analyze an Azure architecture diagram IMAGE_PATH and generate a markdown summary.
    """
    click.secho("🚀 Starting Azure Architecture Workflow...",
                fg="cyan", bold=True)
    workflow = AzureArchitectureWorkflow()
    encoded_image = workflow.encode_image(image_path)
    graph = workflow.graph_builder()
    summary = None
    for message in graph.stream(
            {
                "uploaded_image": encoded_image,
            }, stream_mode=["values"]):
        values = message[1]
        if "messages" in values.keys() and values["messages"]:
            click.secho(values["messages"][-1].content[0]["text"], fg="green")
    message = message[1]
    if "summary" in message.keys() and values["summary"]:
        summary = values["summary"]
        summary = summary.strip('```markdown').strip('```')
        click.secho("\n🎉 Workflow completed. Here's your summary:\n",
                    fg="magenta", bold=True)
        click.echo(summary)
        filename = output or (
            "summary" + time.strftime("%Y%m%d-%H%M%S") + ".md")
        with open(filename, "w") as f:
            f.write(summary)
        click.secho(
            f"\n✅ Summary written to {filename}", fg="yellow", bold=True)
    else:
        click.secho("❌ No summary generated.", fg="red", bold=True)


if __name__ == "__main__":
    analyze()
