# Spica Deep Research MCP Server

An MCP (Model Context Protocol) server that provides AI-powered search and question-answering capabilities using OpenAI Vector Store.

## Features

- **Document Search**: Find relevant documents in your vector store
- **Document Retrieval**: Fetch complete document content with metadata
- **AI Question Answering**: Get intelligent answers based on your document collection

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- OpenAI Vector Store ID

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd deep-research-mcp
   ```

2. Create and activate virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file with your credentials:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   VECTOR_STORE_ID=your_vector_store_id_here
   ```

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "spica-deep-research": {
      "command": "/path/to/your/deep-research-mcp/start-mcp.sh"
    }
  }
}
```

### Manual Testing

You can test the server manually:

```bash
./start-mcp.sh
```

## Available Tools

### 1. `search`

Search for documents in your vector store.

- **Input**: Query string
- **Output**: List of relevant documents with snippets

### 2. `fetch`

Retrieve complete document content by ID.

- **Input**: Document ID (file-xxx format)
- **Output**: Complete document with metadata

### 3. `answer_question`

Get AI-powered answers based on your document collection.

- **Input**: Your question
- **Output**: Comprehensive answer with source citations

## Example Usage in Claude

Once configured, you can ask questions like:

- "Search for documents about authentication"
- "What does the documentation say about API integration?"
- "How do I implement user login functionality?"
- "Fetch the complete content of document file-abc123"

The server will automatically search your vector store, find relevant content, and provide AI-generated answers with proper source citations.

## Configuration

The server uses these environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `VECTOR_STORE_ID`: Your OpenAI Vector Store ID

## Troubleshooting

1. **Module not found errors**: Make sure you've activated the virtual environment and installed requirements
2. **API key errors**: Check your `.env` file and ensure OPENAI_API_KEY is set correctly
3. **Vector store errors**: Verify your VECTOR_STORE_ID is correct and accessible

## Architecture

- **FastMCP**: Framework for building MCP servers
- **OpenAI API**: For vector search and AI completions
- **Stdio Transport**: Communication protocol with Claude Desktop
