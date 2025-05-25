# temusproject7 - AI Research Assistant

> Link: <a href="https://kmoyu.pythonanywhere.com">Research Helper</a>

## 📝 Overview

This project provides an AI-powered research pipeline that creates structured, well-cited reports on any topic. The pipeline:

1. Plans a research outline with key sections
2. Gathers evidence for each section using web search
3. Synthesizes findings into a coherent, well-structured report

The system uses the Groq LLM API for text generation and Tavily for web search, managing token usage to stay within rate limits.

## 🚀 Getting Started - Backend

1.  **Create the virtual environment:**
    ```bash
    uv venv --python 3.12
    ```

2.  **Activate the environment:**
    ```bash
    source .venv/bin/activate
    ```
    *Alternatively, you can use `make activate`, which will spawn a new shell with the environment activated.*

3.  **Install UV (if not already installed):**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    *(You might need to restart your terminal or source your shell profile, e.g., `source ~/.bashrc` or `source ~/.zshrc`, for the `uv` command to be available if it was just installed).*

4.  **Install project dependencies:**
    ```bash
    uv sync
    ```

5.  **Set up API keys:**
    Create a `.env` file in the project root with the following keys:
    ```
    GROQ_API_KEY=your_groq_api_key
    TAVILY_API_KEY=your_tavily_api_key
    ```

6.  **Run the research tool:**
    ```bash
    # With a direct query
    python temusproj/research.py "Will sodium-ion batteries overtake lithium-ion by 2030?"
    
    # Or in interactive mode (will prompt for input)
    python temusproj/research.py
    ```

## ⚙️ Configuration

The research pipeline is highly configurable through the `Config` class in `temusproj/research.py`:

### Model Settings

```python
# Model settings
GROQ_MODEL = "llama3-70b-8192"  # Which Groq model to use
TOKEN_BUDGET = 12_000  # tokens-per-minute for free tier and note the underscores

# Token allocations
PLANNER_TOK = 512      # outline size
WRITER_TOK = 1_024     # each section draft and note the underscores
```

### Prompt Templates

You can modify the system prompts to customize the research style:

```python
# Prompts
PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a meticulous research planner. "
            "Create a bullet-point outline (≤6 bullets) for a report on: {query}. "
            "Return plain bullets, no prose.",
        ),
    ]
)

WRITER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a senior analyst. Write a concise, well-cited answer.\n"
            "Use the <sources></sources> tag to enclose any sources.",
        ),
        ("user", "{draft_instructions}"),
    ]
)
```

## ⚠️ Limitations

### Groq API Rate Limits

- The free tier of Groq API limits usage to **12,000 tokens per minute**
- The pipeline includes automatic rate limiting to stay within this budget
- For larger research projects, consider:
  - Breaking research into smaller queries
  - Upgrading to a paid Groq API tier
  - Modifying the `TOKEN_BUDGET` parameter if you have a higher limit

### Research Depth

- Web search results are limited to 3 sources per outline point
- For more comprehensive research, consider increasing the `k` parameter in `TavilySearchAPIRetriever(k=3)`
- Context length is limited by the model; very complex topics may need multiple research passes

## 🔌 Integration

To integrate the research pipeline directly into your application:

```python
from temusproj.research import ResearchPipeline

# Initialize the pipeline
researcher = ResearchPipeline()

# Run a complete research project
report = researcher.deep_research("Your research question here")
print(report)

# Or use individual components
def custom_research_flow(query):
    # Get outline 
    outline = researcher.plan(query)
    
    # Customize which points to research further
    selected_points = outline[:3]  # Use only first 3 points
    
    # Get evidence
    evidence = {point: researcher.research(point) for point in selected_points}
    
    # Generate report
    return researcher.write(query, selected_points, evidence)
```

### Example Frontend Integration

```python
from flask import Flask, request, jsonify
from temusproj.research import ResearchPipeline

app = Flask(__name__)
researcher = ResearchPipeline()

@app.route('/research', methods=['POST'])
def research_endpoint():
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    
    # For longer queries, you may want to run this in a background worker
    result = researcher.deep_research(query)
    
    return jsonify({
        "query": query,
        "report": result
    })

if __name__ == '__main__':
    app.run(debug=True)
```

## 🧠 Advanced Usage

### Custom Token Budgeting

If you need more fine-grained control over token usage:

```python
# Adjust token allocations for different sections
researcher.config.PLANNER_TOK = 800  # Allow more tokens for complex planning
researcher.config.WRITER_TOK = 1500  # Allow longer section drafts

# For time-sensitive applications, adjust the limiter to use more of your budget
researcher.limiter = Budget(20_000)  # Higher tokens-per-minute if you have a paid tier
```

### Custom Research Pipeline

You can extend the `ResearchPipeline` class to add custom functionality:

```python
class EnhancedResearch(ResearchPipeline):
    def __init__(self, extra_context=""):
        super().__init__()
        self.extra_context = extra_context
    
    def deep_research(self, query):
        # Add your context to every research query
        enriched_query = f"{query} {self.extra_context}"
        return super().deep_research(enriched_query)
```
