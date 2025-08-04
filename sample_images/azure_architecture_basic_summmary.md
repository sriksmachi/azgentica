## **Architecture Summary**
- **Summary**:  
  As an Azure Architect, this architecture diagram represents a system designed to securely interact with Azure AI Foundry services using an App Service instance with built-in authentication and managed identity. The Foundry Agent Service facilitates communication with Azure OpenAI models and Azure AI Search. Monitoring and observability are achieved using Application Insights and Azure Monitor. The architecture aims to provide secure, scalable, and efficient AI-driven functionalities while ensuring operational excellence and cost optimization.  
  **Objectives**:  
  - Secure access to Azure AI Foundry services using managed identity.  
  - Enable AI-driven functionalities via Azure OpenAI and Azure AI Search.  
  - Monitor and optimize system performance using Application Insights and Azure Monitor.  
  **Purpose**:  
  - Deliver AI-powered solutions with robust security and scalability.  
  - Ensure operational excellence through monitoring and diagnostics.  
  **Limitations**:  
  - Limited redundancy and fault tolerance without additional configurations.  
  - Potential cost overhead for production workloads without optimization.  
  **Key Risks**:  
  - Security risks if HTTPS enforcement and private endpoints are not configured.  
  - Performance bottlenecks during peak loads without autoscaling.  

### **Services Used**
| **Service Name**             | **Purpose**                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| Azure App Service             | Hosts the application and provides built-in authentication (Easy Auth).    |
| App Service Instance          | Core component hosting the web application and interacting with services.  |
| Azure AI Foundry Account      | Provides AI Foundry services for the application.                          |
| Foundry Agent Service         | Facilitates communication with Azure OpenAI and AI Search.                 |
| Azure OpenAI Model            | Provides AI-driven functionalities for the application.                    |
| Azure AI Search               | Enables data processing and search indexing.                              |
| Application Insights          | Monitors system performance and provides telemetry data.                   |
| Azure Monitor                 | Provides centralized monitoring and alerting capabilities.                 |

### **Cost Analysis**
- **Summary of Azure Services Cost**:  
  The total monthly cost for the architecture is calculated based on the services used. The cost breakdown highlights the expenses for compute, storage, and networking services.  
- **Total Cost**: **$544.00 USD**  
- **Azure Compute Services Cost**: Azure App Service - $149.00 USD  
- **Azure Storage Services Cost**: Not applicable in this architecture.  
- **Azure Networking Services Cost**: Not applicable in this architecture.  

#### **Azure Services Cost**
| **Service Name**             | **SKU**         | **Quantity** | **Unit Price (USD)** | **Monthly Cost (USD)** | **Assumptions**                                                                 |
|-------------------------------|-----------------|--------------|-----------------------|-------------------------|---------------------------------------------------------------------------------|
| Azure App Service             | P1V3           | 1            | 149.00               | 149.00                 | Production workload with high availability, single instance.                   |
| Azure AI Foundry Account      | Standard       | 1            | 100.00               | 100.00                 | Standard tier for AI Foundry services.                                         |
| Azure OpenAI Model            | Standard       | 1            | 10.00                | 10.00                  | Standard tier for OpenAI model usage.                                          |
| Azure AI Search               | Standard S1    | 1            | 250.00               | 250.00                 | Standard S1 tier for search indexing and querying.                             |
| Application Insights          | Basic          | 1            | 20.00                | 20.00                  | Basic tier for monitoring and telemetry.                                       |
| Azure Monitor                 | Standard       | 1            | 15.00                | 15.00                  | Standard tier for monitoring and alerting.                                     |

### **Service Recommendations**
| **Service Name**             | **Review**                                                                 | **Recommendation**                                                                 | **Pillar in Review**       |
|-------------------------------|---------------------------------------------------------------------------|-----------------------------------------------------------------------------------|----------------------------|
| Azure App Service             | Hosts the application with built-in authentication and managed identity. | Enable zone redundancy, use Premium v3 tier, and define automatic healing rules.  | Reliability                |
| Azure App Service             | Provides secure access to resources.                                     | Integrate with virtual network, enforce HTTPS, and use Azure Key Vault.           | Security                   |
| Azure App Service             | Scales based on demand.                                                  | Use autoscaling, simulate load scenarios, and enable caching mechanisms.          | Performance Efficiency     |
| Azure App Service             | Used for hosting and managing the application.                          | Use free/basic tiers for pre-production, apply reservation discounts, and monitor costs. | Cost                       |
| Azure App Service             | Integrated with Application Insights and Azure Monitor.                 | Enable diagnostic logging, use deployment slots, and validate changes in staging. | Operational Excellence     |
| App Service Instance          | Core component hosting the web application.                             | Use Premium v3 tier, enable Always On, and configure autoscaling rules.           | Reliability                |
| App Service Instance          | Supports built-in authentication and managed identity.                  | Enable Microsoft Defender, enforce HTTPS, and use private endpoints.              | Security                   |
| App Service Instance          | Handles user requests and interacts with Azure AI Foundry services.     | Use Azure pricing calculator, implement autoscaling, and leverage reserved instances. | Cost                       |
| App Service Instance          | Integrated with monitoring tools.                                       | Use CI/CD pipelines, validate changes in staging slots, and enable diagnostic logging. | Operational Excellence     |
| App Service Instance          | Designed to handle user requests and interact with AI Foundry services. | Enable HTTP/2, use caching mechanisms, and conduct load testing.                  | Performance Efficiency     |
| Azure OpenAI Model            | Provides AI capabilities for the application.                          | Enable dynamic quota, monitor token usage, and use provisioned throughput.        | Cost                       |
| Azure OpenAI Model            | Critical for AI functionalities.                                        | Enable Azure Diagnostics and implement automated key rotation.                    | Operational Excellence     |
| Azure OpenAI Model            | Essential for maintaining user experience.                             | Benchmark token consumption and implement streaming for chatbots.                 | Performance Efficiency     |
| Azure OpenAI Model            | Ensures uninterrupted service.                                          | Deploy gateways for redundancy and monitor capacity usage.                        | Reliability                |
| Azure OpenAI Model            | Protects sensitive data.                                                | Use customer-managed keys, disable public access, and implement RBAC.             | Security                   |
| Application Insights          | Monitors system performance and provides telemetry data.                | Use one resource per workload, deploy in the same region, and implement sampling. | Cost                       |
| Application Insights          | Provides observability into the application.                           | Adopt autoinstrumentation and update SDKs annually.                               | Operational Excellence     |
| Application Insights          | Collects telemetry data for monitoring performance.                    | Define performance targets and optimize custom metrics.                           | Performance Efficiency     |
| Application Insights          | Critical for monitoring health and reliability.                        | Create resiliency plans and export logs to backup destinations.                   | Reliability                |
| Application Insights          | Collects telemetry data, including sensitive information.              | Use customer-managed keys, implement private connectivity, and anonymize data.    | Security                   |

### **Nodes**
- **Nodes**:  
```json
[
  {"id": "User", "type": "custom", "label": "User"},
  {"id": "App Service", "type": "azure", "label": "Azure App Service"},
  {"id": "App Service Instance", "type": "azure", "label": "App Service instance"},
  {"id": "Azure AI Foundry Account", "type": "azure", "label": "Azure AI Foundry account"},
  {"id": "Foundry Agent Service", "type": "custom", "label": "Foundry Agent Service"},
  {"id": "Azure OpenAI Model", "type": "azure", "label": "Azure OpenAI model"},
  {"id": "Azure AI Search", "type": "azure", "label": "Azure AI Search"},
  {"id": "Application Insights", "type": "azure", "label": "Application Insights"},
  {"id": "Azure Monitor", "type": "azure", "label": "Azure Monitor"}
]
```

### **Edges**
- **Edges**:  
```json
[
  {"source": "User", "target": "App Service Instance", "label": "HTTP request", "metadata": {"protocol": "HTTPS"}},
  {"source": "App Service Instance", "target": "App Service", "label": "App Service built-in authentication (Easy Auth)"},
  {"source": "App Service Instance", "target": "Foundry Agent Service", "label": "Managed identity"},
  {"source": "Foundry Agent Service", "target": "Azure AI Foundry Account", "label": "Azure AI Foundry project"},
  {"source": "Foundry Agent Service", "target": "Azure OpenAI Model", "label": "API call"},
  {"source": "Azure OpenAI Model", "target": "Azure AI Search", "label": "Data processing"},
  {"source": "App Service Instance", "target": "Application Insights", "label": "Monitoring"},
  {"source": "App Service Instance", "target": "Azure Monitor", "label": "Monitoring"}
]
