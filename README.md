<h1 align="center">Agentic Coding - Project Template</h1>

<p align="center">
  <a href="https://github.com/The-Pocket/PocketFlow" target="_blank">
    <img 
      src="./assets/banner.png" width="600"
    />
  </a>
</p>

This is a project template for Agentic Coding with [Pocket Flow](https://github.com/The-Pocket/PocketFlow), a 100-line LLM framework, and your editor of choice.

- We have included the [.cursorrules](.cursorrules), [.clinerules](.clinerules), and [.windsurfrules](.windsurfrules) files to let Cursor AI (also Cline, or Windsurf) help you build LLM projects.
- Want to learn how to build LLM projects with Agentic Coding?

  - Check out the [Agentic Coding Guidance](https://the-pocket.github.io/PocketFlow/guide.html)
  - Check out the [YouTube Tutorial](https://www.youtube.com/@ZacharyLLM?sub_confirmation=1)

# PocketFlow Web Research Agent

A dynamic web research agent built with PocketFlow that can systematically gather information from the web, synthesize findings, and present reasoned answers to complex queries.

## Overview

This agent is designed to:

1. Receive natural language queries from users
2. Intelligently search for information using various web tools (DuckDuckGo, Google, direct crawling)
3. Extract, analyze, and synthesize the gathered information
4. Present a reasoned answer with supporting evidence and a summary of the research journey
5. Allow for human feedback and iterative refinement

## Features

- **Multi-tool Web Research**: Uses DuckDuckGo, Google Search, and direct web crawling
- **Intelligent Decision Making**: Google Gemini-powered decision node selects the most appropriate research actions
- **Information Synthesis**: Analyzes and structures information from multiple sources
- **Confidence Assessment**: Evaluates the certainty of findings
- **Loop Detection**: Identifies and breaks out of unhelpful research loops
- **Human-in-the-Loop**: Allows for human feedback to guide further research

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pocketflow-webscraper.git
   cd pocketflow-webscraper
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   # Required
   GOOGLE_API_KEY=your_google_api_key_here
   
   # Optional (for Google Search)
   GOOGLE_CSE_ID=your_google_custom_search_engine_id_here
   ```

## Usage

Run the agent with:

```
python main.py
```

The agent will prompt you to enter a research query, then systematically search for information and present its findings.

## Project Structure

- **nodes.py**: Contains all PocketFlow node implementations
- **flow.py**: Defines the research flow and connects the nodes
- **main.py**: Entry point for the application
- **utils/**: Utility functions for web interactions and LLM calls
- **docs/**: Documentation including the design document

## Core Components

1. **QueryInputNode**: Receives the user's query
2. **DecisionNode**: Determines the next research action
3. **Tool Nodes**: Perform web searches and crawling
   - DuckDuckGoSearchNode
   - GoogleSearchNode
   - WebCrawlNode
4. **AnalyzerNode**: Processes results and extracts information
5. **HITLOutputNode**: Generates the final human-readable report
6. **HumanFeedbackNode**: Processes user feedback

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Built with [PocketFlow](https://github.com/the-pocket/PocketFlow)
- Uses Google Generative AI API for LLM capabilities
