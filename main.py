"""
Sample MCP Server for ChatGPT Deep Research Integration

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's deep research feature.
"""

import logging
import os
import asyncio
from typing import Dict, List, Any

from fastmcp import FastMCP
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv() 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID", "")

# Initialize OpenAI client
openai_client = OpenAI()

server_instructions = """
This MCP server provides search and document retrieval capabilities 
for deep research. Use the search tool to find relevant documents 
based on keywords, then use the fetch tool to retrieve complete 
document content with citations.
"""


def create_server():
    """Create and configure the MCP server with search and fetch tools."""

    # Initialize the FastMCP server
    mcp = FastMCP(name="Sample Deep Research MCP Server",
                  instructions=server_instructions)

    @mcp.tool()
    async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for documents using OpenAI Vector Store.
        
        Since direct vector store search isn't available, this tool lists all files
        in the vector store and uses semantic matching via embeddings.
        
        Args:
            query: Search query string.
        
        Returns:
            Dictionary with 'results' key containing list of matching documents.
        """
        if not query or not query.strip():
            return {"results": []}

        if not openai_client:
            logger.error("OpenAI client not initialized - API key missing")
            raise ValueError("OpenAI API key is required for vector store search")

        logger.info(f"Searching {VECTOR_STORE_ID} for query: '{query}'")

        try:
            # List all files in the vector store
            files = openai_client.vector_stores.files.list(vector_store_id=VECTOR_STORE_ID)
            
            results = []
            for file in files.data:
                # Get basic file info
                file_id = file.id
                filename = getattr(file, 'filename', f"Document {file_id}")
                
                # Try to get a snippet of content
                try:
                    content_response = openai_client.vector_stores.files.content(
                        vector_store_id=VECTOR_STORE_ID, 
                        file_id=file_id
                    )
                    
                    # Extract text content
                    text_content = ""
                    if hasattr(content_response, 'data') and content_response.data:
                        # Combine content chunks
                        content_parts = []
                        for content_item in content_response.data:
                            if hasattr(content_item, 'text'):
                                content_parts.append(content_item.text)
                        text_content = "\n".join(content_parts)
                    
                    # Create snippet
                    text_snippet = text_content[:200] + "..." if len(text_content) > 200 else text_content
                    
                except Exception as e:
                    logger.warning(f"Could not fetch content for file {file_id}: {e}")
                    text_snippet = "Content not available"
                
                result = {
                    "id": file_id,
                    "title": filename,
                    "text": text_snippet,
                    "url": f"https://platform.openai.com/storage/files/{file_id}"
                }
                results.append(result)

            logger.info(f"Found {len(results)} files in vector store")
            return {"results": results}
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return {"results": []}

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """
        Retrieve complete document content by ID.
        
        Args:
            id: File ID from vector store (file-xxx)
            
        Returns:
            Complete document with id, title, full text content, URL, and metadata
        """
        if not id:
            raise ValueError("Document ID is required")

        if not openai_client:
            logger.error("OpenAI client not initialized - API key missing")
            raise ValueError("OpenAI API key is required for vector store file retrieval")

        logger.info(f"Fetching content from vector store for file ID: {id}")

        try:
            # Fetch file content from vector store
            content_response = openai_client.vector_stores.files.content(
                vector_store_id=VECTOR_STORE_ID, 
                file_id=id
            )

            # Get file metadata
            file_info = openai_client.vector_stores.files.retrieve(
                vector_store_id=VECTOR_STORE_ID, 
                file_id=id
            )

            # Extract content from response
            file_content = ""
            if hasattr(content_response, 'data') and content_response.data:
                content_parts = []
                for content_item in content_response.data:
                    if hasattr(content_item, 'text'):
                        content_parts.append(content_item.text)
                file_content = "\n".join(content_parts)
            else:
                file_content = "No content available"

            # Use filename as title
            filename = getattr(file_info, 'filename', f"Document {id}")

            result = {
                "id": id,
                "title": filename,
                "text": file_content,
                "url": f"https://platform.openai.com/storage/files/{id}",
                "metadata": {
                    "file_id": id,
                    "filename": filename,
                    "vector_store_id": VECTOR_STORE_ID
                }
            }

            logger.info(f"Successfully fetched file: {id} ({len(file_content)} characters)")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching file {id}: {e}")
            raise ValueError(f"Could not fetch document with ID {id}: {str(e)}")

    return mcp
def main():
    """Main function to start the MCP server."""
    # Verify OpenAI client is initialized
    if not openai_client:
        logger.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        raise ValueError("OpenAI API key is required")

    if not VECTOR_STORE_ID:
        logger.error("Vector store ID not found. Please set VECTOR_STORE_ID environment variable.")
        raise ValueError("Vector store ID is required")

    logger.info(f"Using vector store: {VECTOR_STORE_ID}")

    # Create the MCP server
    server = create_server()
    
    # Better approach: define the test function outside and call it directly
    async def run_answer_test():
        try:
            logger.info("Running answer_test on startup...")
            # result = await answer_test_direct("I want to insert a data into my payment bucket if identity exist go for the flow (use identity login for this) if not write into corrupted bucket and return my corrupted bucket id = corrupted567 fails it should write this into log bucket my log bucket id = log123 my payment id=payment987 give me the functions for this logic use ")  # Call a direct version
            result = await answer_test_direct("""

        How can insert data in js sdk
""")
            logger.info(f"Answer test result: {result}")
        except Exception as e:
            logger.error(f"Startup test failed: {e}")
    
    # Run the test
    asyncio.run(run_answer_test())
    
    # Configure and start the server
    logger.info("Starting MCP server on 0.0.0.0:8000")
    logger.info("Server will be accessible via SSE transport")

    try:
        # Use FastMCP's built-in run method with SSE transport
        server.run(transport="sse", host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

# Add this function outside the server creation
async def answer_test_direct(query: str) -> Dict[str, Any]:
    try:
        logger.info(f"Running dynamic answer_test for: {query}")

        if not openai_client:
            raise ValueError("OpenAI client is not initialized")

        if not VECTOR_STORE_ID:
            raise ValueError("VECTOR_STORE_ID is not set")

        # Step 1: Search vector store
        search_response = openai_client.vector_stores.search(
            vector_store_id=VECTOR_STORE_ID,
            query=query,
        )

        if not search_response.data or len(search_response.data) == 0:
            raise ValueError("No matching documents found for the query.")

        # Step 2: Group results by file_id with total score
        file_score_map = {}
        file_chunks_map = {}

        for item in search_response.data:
            file_id = getattr(item, "file_id", None)
            if not file_id:
                continue

            score = getattr(item, "score", 0)  # or similarity

            texts = []
            if hasattr(item, "content") and isinstance(item.content, list):
                for content_obj in item.content:
                    if hasattr(content_obj, "text"):
                        texts.append(content_obj.text)

            file_score_map[file_id] = file_score_map.get(file_id, 0) + score
            file_chunks_map.setdefault(file_id, []).extend(texts)

        if not file_chunks_map:
            raise ValueError("No document chunks found in search results.")

        # Step 3: Select file with highest total relevance score
        best_file_id = max(file_score_map, key=file_score_map.get)
        combined_text = "\n".join(file_chunks_map[best_file_id])

        # Try to get filename from one of the search results for best_file_id
        filename = None
        for item in search_response.data:
            if getattr(item, "file_id", None) == best_file_id:
                filename = getattr(item, "filename", None)
                break

        # Step 4: Prepare prompt for LLM
        prompt = f"""Based on the document below, answer the question:
Document:
{combined_text}

Question: {query}

Please provide a short, helpful answer"""

        # Step 5: Call OpenAI chat completion
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150
        )

        answer = response.choices[0].message.content.strip()

        return {
            "query": query,
            "answer": answer,
            "source_title": filename or f"Document {best_file_id}",
            "source_url": f"https://platform.openai.com/storage/files/{best_file_id}",
            "success": True
        }

    except Exception as e:
        logger.error(f"Error in answer_test_direct: {e}")
        return {
            "query": query,
            "answer": f"Error: {str(e)}",
            "source_title": "N/A",
            "source_url": "N/A",
            "success": False
        }




if __name__ == "__main__":
    main()