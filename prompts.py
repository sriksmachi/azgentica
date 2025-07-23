
data_extraction_prompt = """
You are a vision-language model specialized in reading architecture diagrams and extracting their components.
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

3. **Analyze the architecture** as an Architect and describe in detail so that it can be used to re-create the architecture.
   - Provide a elaborated description of the architecture.
   - Include the purpose of each component and how they interact.
   - List the information in a pointed format for clarity.
   - If any components are grouped or placed within a subnet, note that relationship.

4. **Output the extracted data** in the following JSON format:
```json
{
  "description": "A detailed description of the architecture diagram.",
  "nodes": [
    {"id": "App Service", "type": "azure", "label": "Azure App Service"},
    {"id": "OpenAI", "type": "azure", "label": "Azure OpenAI Service"},
    {"id": "Custom Agent", "type": "custom", "label": "Foundry Agent Service"},
    ...
  ],
  "edges": [
        {"source": "App Service", "target": "OpenAI", "label": "HTTP request"},
        {"source": "OpenAI", "target": "Custom Agent", "label": "API call"},
        ...
  ]  
}

5. **Additional Guidelines**
- If any element is visually grouped or placed within a subnet, add that relationship as metadata. 
- Perform OCR for custom components or blocks with text. 
- Add `"subnet"` or `"zone"` as an optional field in nodes. 
- Use `"metadata"` field in edges to include optional notes like protocol (HTTPS, REST, etc.)
"""

# Failed attempt to generate draw.io XML from image
draw_io_generation_prompt = """
You are an expert in analyzing Azure architecture diagrams and converting them to draw.io compatible XML. 
Your task is to extract key components and their relationships from the Azure architecture diagram provided in the image and generate a XML representation of the architecture compatible with draw.io.
The image will be in base64 format. 

Sample Draw.io format: 
```xml
<mxfile host="app.diagrams.net">
  <diagram name="Page-1" id="Page-1">
    <mxGraphModel dx="1420" dy="1020" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" parent="1" />
        <mxCell id="1" parent="0" />
        <mxCell id="2" value="Azure App Service" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#00A4EF;strokeColor=#000000;" vertex="1" parent="1" description="Azure App Service is a fully managed platform for building, deploying, and scaling web apps. It supports multiple programming languages and frameworks, making it easy to host web applications without managing the underlying infrastructure.">
          <mxGeometry x="20" y="20" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="3" value="Azure OpenAI Service" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#00A4EF;strokeColor=#000000;" vertex="1" parent="1" description="Azure OpenAI Service provides advanced AI capabilities, including natural language understanding and generation, enabling developers to build intelligent applications.">
          <mxGeometry x="200" y="20" width="120" height="60" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>

Instructions:
1. Identify all Azure services, components, and their relationships in the architecture diagram.
2. Generate a draw.io compatible XML structure that represents the architecture using the image. 
3. Represent each component as basic shape with appropriate labels and types. Do not use complex shapes or images.
4. Ensure the XML is well-formed and includes all necessary elements to represent the architecture accurately
4. Provide the XML output in a code block with the language set to "xml" for easy readability.
5. Do not include any additional text or explanations outside the code block.
6. The stucture of the XML should follow the provided sample structure.
7. Do not miss any components or relationships, even if they are not explicitly labeled in the image.
8. Group components that are visually clustered together in the architecture diagram, and represent them as a single node in the XML.
9. Make sure the arrows do not overlap with the nodes and other arrows in the XML.
10. Use different colors for different types of nodes (e.g., Azure services, custom components, external services) to enhance readability.
11. Describe the importance of each component in the architecture and how they interact with each other in the Node, Edge Description.
"""


json_output_format = """
[
    {
        "service": "Service Name",
        "sku": "SKU of the service",
        "quantity": "Quantity of the service",
        "unit_price": "Unit price of the service",
        "monthly_cost": "Estimated monthly cost for the service",
        "currency": "Currency of the cost (e.g., USD)",
        "assumptions": "Assumptions made for the cost calculation (e.g., high availability, redundancy)"
    }
]
"""

cost_calculation_prompt = """
    You are an expert in Azure architecture and cost estimation. Given the services in JSON format as input, \
    Calculate the estimated monthly cost for running the services in Azure. Use existing knowledge to find the latest pricing information for each service. \
    Provide the cost breakdown for each service and the total estimated monthly cost. Input : {data}

    Output Format: {json_output_format}

    Instructions:
    1. Analyze the provided JSON input to identify the services and their configurations.
    2. For each service, determine the SKU, quantity, and unit price based on Azure's pricing model.
    3. Calculate the monthly cost for each service based on the quantity and unit price.
    4. Assume the application will be deployed in Production mode with high availability and redundancy and suggest appropriate SKUs for production workloads.
    5. Provide the final output in the specified JSON format
    6. Do not include any additional text or explanations in the output, only the JSON response.
"""
