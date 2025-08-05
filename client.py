from openai import OpenAI
from dotenv import load_dotenv
from dotenv import dotenv_values
import re
import os

load_dotenv()

# Load from .env
env = dotenv_values(".env")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
FILE_ID = os.getenv("FILE_ID")

if not VECTOR_STORE_ID:
    raise ValueError("❌ VECTOR_STORE_ID is missing in .env")

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORG_ID")
)
print("🔍 API Key loaded:", os.getenv("OPENAI_API_KEY")[:10], "...")
print("🔍 Org ID loaded:", os.getenv("OPENAI_ORG_ID"))
def get_file_content(file_id):
    """Get the full content of a file"""
    try:
        content = client.vector_stores.files.content(
            vector_store_id=VECTOR_STORE_ID,
            file_id=file_id
        )
        
        full_text = ""
        if hasattr(content, 'data') and content.data:
            for chunk in content.data:
                if hasattr(chunk, 'text'):
                    full_text += chunk.text + "\n"
        
        return full_text.strip()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def simple_answer_extractor(content, question):
    """
    Simple rule-based answer extraction (no API calls needed)
    This shows what your MCP tool SHOULD do vs what it's currently doing
    """
    content_lower = content.lower()
    question_lower = question.lower()
    
    if "how long can cat live" in question_lower:
        # Find the first sentence that defines what a cat is
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            if 'cat' in sentence.lower() and ('are' in sentence.lower() or 'is' in sentence.lower()):
                return sentence.strip() + "."
    
    # Fallback: return first 2 sentences
    sentences = re.split(r'[.!?]+', content)
    if len(sentences) >= 2:
        return sentences[0].strip() + ". " + sentences[1].strip() + "."
    
    return "Could not extract a concise answer."

def demonstrate_mcp_behavior():
    """Demonstrate what MCP tools should return vs what they currently return"""
    
    print("🚀 MCP Behavior Demonstration")
    print("="*50)
    
    # Get the file content (this is what fetch() returns)
    content = get_file_content(FILE_ID)
    
    if not content:
        print("❌ Could not retrieve file content")
        return
    
    print("\n📄 What the `fetch()` tool returns:")
    print("="*30)
    print(content)
    print(f"\n📏 Length: {len(content)} characters")
    
    print("\n🤖 What the `answer_test()` tool SHOULD return:")
    print("="*35)
    
    # This simulates what your answer_test() tool should do
    question = "What is a cat?"
    simple_answer = simple_answer_extractor(content, question)
    
    mock_response = {
        "query": question,
        "answer": simple_answer,
        "source_title": "Document about cats",
        "source_url": f"https://platform.openai.com/storage/files/{FILE_ID}",
        "success": True
    }
    
    print(f"Question: {mock_response['query']}")
    print(f"Answer: {mock_response['answer']}")
    print(f"Source: {mock_response['source_title']}")
    print(f"Length: {len(mock_response['answer'])} characters")
    
    print("\n🔍 The Key Difference:")
    print("="*25)
    print("❌ WRONG: MCP returning entire document (what you're seeing now)")
    print("✅ CORRECT: MCP returning processed, concise answer")
    print(f"   • Full document: {len(content)} characters")
    print(f"   • Processed answer: {len(simple_answer)} characters")
    print(f"   • Reduction: {((len(content) - len(simple_answer)) / len(content) * 100):.1f}%")

def test_mcp_tools_simulation():
    """Simulate what your MCP tools should return"""
    
    print("\n🛠️  MCP Tools Simulation")
    print("="*30)
    
    # Simulate search() tool
    print("\n1. search('cat information') should return:")
    search_result = {
        "results": [
            {
                "id": FILE_ID,
                "title": "Document about cats",
                "text": "Cats are small, carnivorous mammals that are often kept as pets...",
                "url": f"https://platform.openai.com/storage/files/{FILE_ID}"
            }
        ]
    }
    print(f"   • {len(search_result['results'])} results")
    print(f"   • First result: {search_result['results'][0]['text']}")
    
    # Simulate fetch() tool
    print("\n2. fetch('{FILE_ID}') returns:")
    print("   • Full document content (what you're seeing)")
    print("   • This is CORRECT behavior for fetch()")
    
    # Simulate answer_test() tool  
    print("\n3. answer_test() should return:")
    print("   • Processed, concise answer")
    print("   • This is FAILING due to quota issues")
    
    print("\n💡 Solution:")
    print("="*15)
    print("1. Fix your OpenAI quota/billing")
    print("2. Test answer_test() tool again")
    print("3. It should return a short answer, not the full document")

if __name__ == "__main__":
    demonstrate_mcp_behavior()
    test_mcp_tools_simulation()