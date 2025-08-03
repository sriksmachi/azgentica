import base64
import os
import json
import logging
import pandas as pd
from dotenv import load_dotenv
from typing import Literal
from typing_extensions import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_openai import AzureChatOpenAI
from langchain_ollama import ChatOllama


from prompts import data_extraction_prompt, cost_calculation_prompt, json_output_format

from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        self.OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llava:7b")
        self.model_type = os.getenv("MODEL_TYPE", "ollama")
        if self.model_type not in ["ollama", "azure"]:
            raise ValueError(
                "Invalid MODEL_TYPE. Supported values are 'ollama' or 'azure'.")

        if self.model_type == "ollama":
            self.llm_client = ChatOllama(
                model=self.OLLAMA_MODEL_NAME,
                temperature=0.3
            )
        elif self.model_type == "azure":
            self.llm_client = AzureChatOpenAI(
                azure_deployment=self.AZURE_OPENAI_DEPLOYMENT_NAME,
                api_version="2024-08-01-preview",
                temperature=0.3,
                model_name=self.AZURE_OPENAI_DEPLOYMENT_NAME,
                azure_endpoint=self.AZURE_OPENAI_ENDPOINT,
                api_key=self.AZURE_OPENAI_API_KEY,
            )

        self.checkpointer = InMemorySaver()
        self.store = InMemoryStore()
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
        # Iterate through each row in the DataFrame
        for _, row in df.iterrows():
            source_words = set(str(row['heading']).lower().split())
            # Simple key phrase matching
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
                             "text": f"Extracted data from image, transferring to supervisor node."},
                        ]
                    )]
            },
            goto="supervisor",
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
                             "text": f"Cost analysis completed, transferring to supervisor node."},
                        ]
                    )]
            },
            goto="supervisor",
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
                                    "url": f"data:image/jpeg;base64,{state['uploaded_image']}"
                                },
                            },
                        ])
                ]
                result = self.llm_client.invoke(new_message)
                result_content_json = json.loads(
                    self.clean_json_string(result.content))
                generated_service_recommendations.extend(result_content_json)
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
            goto="supervisor"
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

                        ## Data: {state}

                        ## State Description:
                        - **Image Description**: Description of the architecture diagram.
                        - **Nodes**: Azure services and their details.
                        - **Edges**: Connections between the services.
                        - **Azure Services Cost**: Cost of each Azure service used in the architecture.
                        - **Service Recommendations**: Recommendations for each service based on the Azure Well-Architected Framework. Each recommendation should include:
                            - **Service Name**: Name of the Azure service.
                            - **Review**: Review of the service.
                            - **Recommendation**: Recommendation for the service.
                            - **Pillar in Review**: Pillar in review (Cost, Operational Excellence, Performance Efficiency, Reliability, Security).
                        - **Summary**: Summary of the architecture diagram including the image description, architecture description, services used, cost analysis, and service recommendations.

                        ## Instructions:
                        - Provide a comprehensive summary of the architecture diagram.
                        - Remember the data could be empty in few areas in the state, so handle it gracefully.
                        - Only fill the data that is available in the state.
                        - Do not include any data that is not available in the state.
                        - Only use the data provided in the state to summarize. Do not make assumptions or add any additional information from your knowledge.

                        ## Formatting instructions:
                        - Use markdown format for the summary.
                        - Use headings to separate different sections of the summary.
                        - Use bullet points for lists.
                        - Convert Service Recommendations to a structured table format.
                        - Convert Azure Services Cost to a structured table format.
                        - Convert Nodes as list of dictionaries.

                        ## Format of the summary should be in markdown format as follows:

                        ### Architecture Summary
                        - **Image Description**:  <<Image description here>>

                        - **Architecture Description**: <<Description of the architecture diagram>>

                        - **Services Used**: <<List of services used in the architecture diagram>>

                        ### Cost Analysis
                        - **Summary of Azure Services Cost**: Create a summary of Azure services cost, total cost per month, and cost breakdown by service. \
                            
                        - **Total Cost**: <<Total cost of the architecture diagram>>
                        - **Azure Compute Services Cost**: <<Data should be in text format>>
                        - **Azure Storage Services Cost**: <<Data should be in text format>>
                        - **Azure Networking Services Cost**: <<Data should be in text format>>
                        
                        - **Azure Services Cost**:  <<Individual Azure service cost, should be in table format>>

                        ### Service Recommendations
                        - **Recommendations**: <<Data should be in table format>>
                        """,
                    }
                ]
            )
        ]
        result = self.llm_client.invoke(messages)
        return Command(
            update={
                "summary": result.content,
                "messages": [
                    SystemMessage(
                        content=[
                            {"type": "text",
                             "text": f"Summarization completed, transferring to supervisor node."},
                        ]
                    )]
            },
            goto="supervisor"
        )

    def supervisor_node(self, state: GraphState):
        system_prompt = (
            f"""You are a supervisor tasked with using the members: {', '.join(self.members)} to process the architecture diagram so that the state: {state} is updated. \
        The members are available to process the state and update it. \
        The members are: {', '.join(self.members)}. \
        If no members are needed, route to FINISH. \
        The next worker to route to is based on the state and the available members. \

        Current state: {state} \

        Follow these rules to route to the next worker: \
        1. If the state has no uploaded image, route to 'data_extraction'
        2. If the state has an uploaded image, route to 'cost_analysis' to calculate the cost of the architecture diagram. \
        3. If the state has an uploaded image and cost analysis is done, route to 'service_recommendations_supervisor_node' to generate service recommendations based on the architecture diagram and cost analysis. \
        4. If the state has an uploaded image, cost analysis is done, and service recommendations are generated, route to 'summarize_results' to summarize the results of the data extraction and cost analysis. \
        6. If the state has an uploaded image, cost analysis is done, service recommendations are generated, and summarization is done, route to 'FINISH' to complete the workflow. \
            """
        )
        messages = [{"role": "system", "content": system_prompt}]
        summarization_agent_response = self.summarize_results(state)
        response = self.llm_client.with_structured_output(
            Router).invoke(messages)
        goto = response["next"]
        logger.info(f"Next Worker: {goto}")
        if goto == "FINISH":
            goto = END
        return Command(goto=goto,
                       update={
                           "summary": summarization_agent_response.update["summary"],
                           "messages": [
                               SystemMessage(
                                   content=[
                                       {"type": "text",
                                        "text": f"Supervisor identified next best action, transferring to {goto}."},
                                   ]
                               )]
                       })

    def graph_builder(self):
        graph_builder = StateGraph(GraphState)
        graph_builder.add_node("data_extraction", self.extract_data_from_image)
        graph_builder.add_node("cost_analysis", self.get_cost_analysis_prompt)
        graph_builder.add_node("service_recommendations_supervisor_node",
                               self.service_recommendations_supervisor_node)
        graph_builder.add_node("summarize_results", self.summarize_results)
        graph_builder.add_node("supervisor", self.supervisor_node)
        graph_builder.add_edge(START, "data_extraction")
        graph = graph_builder.compile()
        return graph


if __name__ == "__main__":
    workflow = AzureArchitectureWorkflow()
    image_path = "sample_images/azure_architecture_basic.png"
    encoded_image = workflow.encode_image(image_path)
    graph = workflow.graph_builder()
    for message in graph.stream(
            {
                "uploaded_image": encoded_image,
            }, stream_mode=["values"]):
        values = message[1]
        if "messages" in values.keys() and values["messages"]:
            print(values["messages"][-1].content[0]["text"])
    message = message[1]
    if "summary" in message.keys() and values["summary"]:
        print(values["summary"])
    print("Workflow completed.")
