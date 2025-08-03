# 🔷 Azgentica

**Azgentica** is a vision-powered intelligent agent for Azure architecture diagrams. It extracts services, components, and their interconnectivity, generating a structured graph in JSON format for visualization, validation, and automation.

---

## 🚀 Features

- 🧠 **AI-Powered Diagram Parsing**  
  Uses `workflow.py` to analyze Azure-native services, custom components, and visual groupings in complex diagrams.

- 🌐 **Node & Edge Extraction**  
  Identifies services as nodes and connections as labeled edges with semantic understanding using `workflow.py`.

- 📊 **Graph Output in JSON**  
  Outputs a structured JSON representation of your architecture for use with NetworkX or other graph libraries.

- 🎯 **Auto-Labeled Relationships**  
  Detects and labels edge types like `private endpoint`, `identity access`, `data flow`, `AI inference`, and more.

- 🛠️ **Streamlit Web App**  
  Use `streamlit_app.py` for an interactive UI to upload diagrams and visualize extracted architecture graphs.

- ⚡ **Data Pipeline**  
  Run `datapipeline.py` to process and transform architecture data for downstream analysis or automation.

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
   - Or process directly with `workflow.py`:
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
* [ ] CLI + Web interface for uploads

### Local & Self-Hosted Options
* [ ] Ollama Support for local model inference
* [ ] Docker containerization

### Advanced Features
* [ ] Real-time architecture validation
* [ ] Security compliance checking

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

