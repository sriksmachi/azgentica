# 🔷 Azgentica

**Azgentica** is a vision-powered intelligent agent for Azure architecture diagrams. It extracts services, components, and their interconnectivity, generating a structured graph in JSON format for visualization, validation, and automation.

---

## 🚀 Features
- 🧠 **AI-Driven Diagram Intelligence**  
  Leverages advanced visual language models to automatically interpret Azure architecture diagrams, accelerating understanding of complex cloud environments.

- 🤖 **

- 🌐 **Semantic Graph Extraction**  
  Transforms visual elements into a structured graph (nodes and edges), enabling precise mapping of services, components, and their relationships for deeper architectural insights.

- 📊 **Actionable JSON Output**  
  Produces a standardized JSON representation, streamlining integration with analytics tools and supporting automated validation, visualization, and documentation workflows.

- 💸 **Built-In Cost & Optimization Analysis**  
  Instantly evaluates extracted architectures for Azure service costs and optimization opportunities, empowering architects to make informed, value-driven decisions.

- 

---

## 📦 Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/sriksmachi/azgentica
cd azgentica
pip install -r requirements.txt
```

---

## 🖼️ How It Works

1. **Upload an Azure architecture diagram (PNG/JPG):**
   - Use the Streamlit app:  
     ```bash
     streamlit run streamlit_app.py
     ```
   - Or process directly with `workflow.py` to view the results in command line:
     ```bash
     python workflow.py --input path/to/diagram.png
     ```

2. **Extract architecture data:**
   - Services, components, and connections are parsed and output as JSON.

3. **Run the data pipeline:**
   - Transform and analyze extracted data:
     ```bash
     python datapipeline.py --input extracted.json --output processed.json
     ```

---

## 📈 Visualization Example (NetworkX)

```python
import networkx as nx
import matplotlib.pyplot as plt
from azgentica import load_architecture_json

G = nx.DiGraph()
# Add nodes/edges from JSON and draw using NetworkX
...
```

---

## 🧩 Use Cases

* ✅ Auto-generate architecture graphs
* 📚 Maintain accurate documentation
* 🔍 Validate connectivity & security design
* 🧠 Feed into downstream AI for cost or performance optimization

---

## 🛡️ Roadmap

### Core Features
* [ ] ARM/Bicep code generation
* [ ] Chat with AI to generate actionables and Infra scripts to improve WAF score in any one area. 
* [ ] Semantic match for finding Azure service recommendations

### Local & Self-Hosted Options
* [ ] Docker containerization

---

## 🤝 Contributing

We welcome contributions! Please open an issue, submit a PR, or suggest improvements via discussions.

---

## 📄 License

MIT License

---

## 🧠 About

**Azgentica** is built for cloud architects, platform engineers, and AI developers who need fast, reliable visibility into complex Azure systems.

> *Visualize. Decode. Optimize.* 🔍🚀

