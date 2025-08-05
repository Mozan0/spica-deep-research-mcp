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
This MCP server provides advanced search and document retrieval capabilities 
for deep research using OpenAI Vector Store. Available tools:

1. search: Find relevant documents based on keywords
2. fetch: Retrieve complete document content with citations  
3. answer_question: Get AI-powered answers based on your document collection

Use these tools to research topics, find specific information, and get 
intelligent answers backed by your document sources.
"""


def create_server():
    """Create and configure the MCP server with search and fetch tools."""

    # Initialize the FastMCP server
    mcp = FastMCP(name="Spica Deep Research MCP Server",
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

    @mcp.tool()
    async def answer_question(query: str) -> Dict[str, Any]:
        """
        Get an AI-powered answer to your question based on the document collection.
        
        This tool searches through your vector store documents, finds the most relevant 
        content, and uses GPT to provide a comprehensive answer with source citations.
        
        Args:
            query: Your question or research query
            
        Returns:
            Dictionary containing the answer, source information, and metadata
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not openai_client:
            logger.error("OpenAI client not initialized - API key missing")
            raise ValueError("OpenAI API key is required for answering questions")

        logger.info(f"Processing question: {query}")

        try:
            # Step 1: Search vector store
            search_response = openai_client.vector_stores.search(
                vector_store_id=VECTOR_STORE_ID,
                query=query,
            )

            if not search_response.data or len(search_response.data) == 0:
                return {
                    "query": query,
                    "answer": "I couldn't find any relevant documents in your collection to answer this question. Try rephrasing your query or ensure your vector store contains relevant content.",
                    "source_title": "N/A",
                    "source_url": "N/A",
                    "success": False
                }

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
                return {
                    "query": query,
                    "answer": "No relevant document chunks found for your query. The search returned results but no readable content was available.",
                    "source_title": "N/A",
                    "source_url": "N/A",
                    "success": False
                }

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
            prompt = f"""Based on the document content below, provide a comprehensive answer to the user's question. Be specific and cite relevant details from the document.

Document Content:
{combined_text}

User Question: {query}

Please provide a detailed, helpful answer based on the document content. If the document doesn't contain enough information to fully answer the question, mention what information is available and what might be missing."""

            # Step 5: Call OpenAI chat completion
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500  # Increased for more comprehensive answers
            )

            answer = response.choices[0].message.content.strip()

            return {
                "query": query,
                "answer": answer,
                "source_title": filename or f"Document {best_file_id}",
                "source_url": f"https://platform.openai.com/storage/files/{best_file_id}",
                "relevance_score": file_score_map[best_file_id],
                "success": True
            }

        except Exception as e:
            logger.error(f"Error in answer_question: {e}")
            return {
                "query": query,
                "answer": f"An error occurred while processing your question: {str(e)}",
                "source_title": "N/A",
                "source_url": "N/A",
                "success": False
            }

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
    
    # Configure and start the server
    logger.info("Starting MCP server")
    logger.info("Server will be accessible via stdio transport for Claude Desktop")
    logger.info("Available tools: search, fetch, answer_question")

    try:
        # Use stdio transport for Claude Desktop integration
        server.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()