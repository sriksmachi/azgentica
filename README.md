# 🔷 Azgentica

**Azgentica** is a vision-powered intelligent agent that analyzes Azure architecture diagrams and extracts all services, components, and their interconnectivity. It generates a clean, structured graph in JSON format, which can be directly used with NetworkX or other graph libraries for visualization, validation, and automation.

---

## 🚀 Features

- 🧠 **AI-Powered Diagram Parsing**  
  Understands Azure-native services, custom components, and visual groupings in complex architecture diagrams.

- 🌐 **Node & Edge Extraction**  
  Identifies services as nodes and connections as labeled edges with semantic understanding (e.g., “AI inference”, “private endpoint”).

- 📊 **Graph Output in JSON**  
  Outputs a fully structured JSON representation of your architecture:  
  ```json
  {
    "nodes": [...],
    "edges": [...]
  }
  ```

* 🎯 **Auto-Labeled Relationships**
  Detects and labels edge types like `private endpoint`, `identity access`, `data flow`, `AI inference`, and more.

* 🛠️ **Built for Azure Architects & DevOps**
  Use it to validate architecture, automate documentation, or generate interactive network graphs.

---

## 📦 Installation

Coming soon as a Python package and web-based tool. For now, clone the repo and run the scripts locally.

```bash
git clone https://github.com/sriksmachi/azgentica
cd azgentica
```

---

## 🖼️ How It Works

1. Upload an Azure architecture diagram (PNG/JPG).
2. Azgentica extracts:

   * All services (Azure, custom, and third-party)
   * All connections (arrows, lines, labeled flows)
3. Returns structured data like:

```json
{
  "nodes": [
    {"id": "AppService", "label": "Azure App Service", "type": "azure"},
    {"id": "OpenAI", "label": "Azure OpenAI Service", "type": "azure"},
    {"id": "CustomAgent", "label": "Foundry Agent", "type": "custom"}
  ],
  "edges": [
    {"source": "AppService", "target": "OpenAI", "label": "AI inference"},
    {"source": "User", "target": "AppService", "label": "HTTP via Gateway"}
  ]
}
```

---

## 📈 Visualization Example (NetworkX)

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load JSON from Azgentica
from azgentica import load_architecture_json

G = nx.DiGraph()
# Add nodes/edges from JSON and draw using NetworkX
...
```

---

## 🧩 Use Cases

* ✅ Auto-generate architecture graphs
* 📚 Maintain accurate architecture documentation
* 🔍 Validate connectivity & security design
* 🧠 Feed into downstream AI for cost or performance optimization

---

## 🛡️ Roadmap

* [ ] CLI + Web interface for uploads
* [ ] Drag-and-drop architecture builder
* [ ] ARM/Bicep code generation
* [ ] Graph comparison (e.g., planned vs. deployed)

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

