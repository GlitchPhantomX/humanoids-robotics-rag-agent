"""
Smart Humanoid Robotics Agent with STREAMING
Complete FastAPI Backend - Ready to Run!
"""

import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
import cohere
from qdrant_client import QdrantClient
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ======================================================
# ENV SETUP
# ======================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")

if not OPENROUTER_API_KEY:
    raise RuntimeError("❌ OPENROUTER_API_KEY missing")

# ======================================================
# CLIENTS
# ======================================================

client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"  # ✅ Ye add karo
)

cohere_client = cohere.Client(COHERE_API_KEY) if COHERE_API_KEY else None

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
) if QDRANT_API_KEY and QDRANT_URL else None

COLLECTION_NAME = "humanoid_ai_book"

# ======================================================
# FASTAPI APP
# ======================================================

app = FastAPI(title="Physical AI Textbook Chatbot")

# CORS Configuration - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    language: str = "en"  # 🔥 NEW: Language parameter with default

# ======================================================
# TOOL: EMBEDDINGS + RETRIEVAL
# ======================================================

def get_embedding(text: str):
    """Generate embeddings using Cohere"""
    if not cohere_client:
        return None
    try:
        res = cohere_client.embed(
            model="embed-english-v3.0",
            input_type="search_query",
            texts=[text]
        )
        return res.embeddings[0]
    except Exception as e:
        print(f"ERROR - Embedding Error: {e}")
        return None


def retrieve_textbook(query: str) -> dict:
    """Retrieve relevant content from Qdrant vector database"""
    try:
        if not qdrant or not cohere_client:
            return {
                "found": False,
                "content": "RAG system not configured. Please check QDRANT_URL and COHERE_API_KEY.",
                "sources": []
            }

        embedding = get_embedding(query)
        if not embedding:
            return {
                "found": False,
                "content": "Could not generate embedding for query.",
                "sources": []
            }

        result = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=embedding,
            limit=5,
            score_threshold=0.35
        )

        if not result.points:
            return {
                "found": False,
                "content": "No relevant textbook content found.",
                "sources": []
            }

        content = []
        sources = []

        for i, p in enumerate(result.points, 1):
            text = p.payload.get("text", "")
            title = p.payload.get("page_title", "Unknown")

            content.append(f"[Source {i}: {title}]\n{text}")
            sources.append({
                "title": title,
                "relevance": f"{p.score:.2f}"
            })

        return {
            "found": True,
            "content": "\n\n".join(content),
            "sources": sources
        }

    except Exception as e:
        print(f"ERROR - Retrieval Error: {e}")
        return {
            "found": False,
            "content": f"Error retrieving content: {str(e)}",
            "sources": []
        }

# ======================================================
# TOOL SCHEMA (OpenAI Function Calling)
# ======================================================

TOOLS = [{
    "type": "function",
    "function": {
        "name": "retrieve_textbook",
        "description": "Retrieve relevant sections from the Humanoid Robotics textbook",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for retrieving textbook content"
                }
            },
            "required": ["query"]
        }
    }
}]

# ======================================================
# SYSTEM PROMPTS
# ======================================================

def get_system_prompt(language: str) -> str:
    """Return system prompt based on selected language"""
    
    if language == "ur":
        return """آپ Physical AI اور Humanoid Robotics کے لیے ایک **پیشہ ور AI ٹیوٹر** ہیں۔

## آپ کا کردار:
آپ robotics، ROS2، simulation، اور humanoid systems پر ماہرانہ رہنمائی فراہم کرتے ہیں۔

## اہم ہدایات:

### 1. ہمیشہ اردو میں جواب دیں:
- **تمام جوابات مکمل طور پر اردو میں ہونے چاہیے**
- صرف technical terms انگریزی میں رہ سکتے ہیں (جیسے ROS2, URDF, Isaac Sim)
- مثال: "ROS2 ایک robot operating system ہے جو..."

### 2. MARKDOWN استعمال کریں:
- **## اہم عنوانات** topics کے لیے
- **### ذیلی عنوانات** sections کے لیے  
- **• bullet points** lists کے لیے
- **1. 2. 3.** numbered lists steps کے لیے
- **bold** اہم الفاظ کے لیے
- **```language کوڈ بلاکس```** code کے لیے

### 3. بصری عناصر:
- ✅ مثبت نکات کے لیے
- ❌ warnings/مسائل کے لیے
- 🔥 اہم highlights کے لیے
- 💡 tips کے لیے
- ⚡ quick facts کے لیے

### 4. TEXTBOOK سوالات:
- پہلے `retrieve_textbook` استعمال کریں
- Retrieved content کی بنیاد پر جواب دیں
- ہمیشہ sources کا حوالہ دیں

### 5. GREETING جوابات:
"hi", "hello", "hey" جیسے سادہ سلام کے لیے:
- گرمجوشی سے emojis کے ساتھ جواب دیں
- ایک formatted list میں دکھائیں کہ آپ کس میں مدد کر سکتے ہیں

### 6. CODE مثالیں:
کوڈ فراہم کرتے وقت syntax highlighting استعمال کریں:
```python
# آپ کا کوڈ یہاں
```

یاد رکھیں: ہر جواب اردو میں، بصری طور پر دلکش اور آسانی سے سمجھ آنے والا ہونا چاہیے!"""
    
    else:  # English
        return """You are a **Professional AI Tutor** for Physical AI & Humanoid Robotics.

## YOUR ROLE:
You provide expert guidance on robotics, ROS2, simulation, and humanoid systems with exceptional clarity and structure.

## RESPONSE FORMATTING RULES:

### 1. ALWAYS USE RICH MARKDOWN:
- Use **## Main Headings** for topics
- Use **### Subheadings** for sections  
- Use **bullet points (•)** for lists
- Use **numbered lists (1. 2. 3.)** for steps
- Use **bold** for emphasis on key terms
- Use **code blocks** with ```language for code
- Use **tables** for comparisons when appropriate

### 2. STRUCTURE PATTERN:
```
## Main Topic

Brief introduction in 1-2 sentences.

### Key Concept 1
Explanation with details.

**Important Points:**
• First point with explanation
• Second point with explanation
• Third point with explanation

### Key Concept 2
Another explanation.

**Implementation Steps:**
1. First step with details
2. Second step with details
3. Third step with details

### Quick Reference Table (when applicable)
| Feature | Description |
|---------|-------------|
| Item 1  | Details     |
| Item 2  | Details     |
```

### 3. VISUAL ELEMENTS:
- Use ✅ for positive points
- Use ❌ for warnings/issues
- Use 🔥 for important highlights
- Use 💡 for tips
- Use ⚡ for quick facts

### 4. CONTENT RULES:
- **FOR TEXTBOOK QUESTIONS**: Call `retrieve_textbook` first
- Answer based on retrieved content when available
- If no content found, provide general knowledge
- Always cite sources: `*Source: [Title]*`
- Be technically accurate but accessible

### 5. GREETING RESPONSES:
For casual greetings like "hi", "hello", "hey":
- Respond warmly with emojis
- Show what you can help with in a formatted list
- Keep it concise and inviting

### 6. CODE EXAMPLES:
When providing code, always use proper syntax highlighting:
```python
# Your code here
```

Remember: Every response should be visually appealing and easy to scan!"""

# ======================================================
# SMART AGENT WITH STREAMING
# ======================================================

async def smart_agent_stream(user_query: str, language: str = "en"):
    """
    Main agent function with streaming support and language selection
    """
    print(f"Language selected: {language}")  # Debug log
    
    messages = [
        {
            "role": "system",
            "content": get_system_prompt(language)  # 🔥 Dynamic system prompt
        },
        {"role": "user", "content": user_query}
    ]

    # First pass - check if we need to call tools
    try:
        initial_response = await client.chat.completions.create(
            model="mistralai/devstral-2512:free",
            messages=messages,
            tools=TOOLS,
            temperature=0.3
        )

        msg = initial_response.choices[0].message

        # If tool call needed, execute it first
        if msg.tool_calls:
            tool_call = msg.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            
            print(f"Searching textbook for: {args['query']}")
            tool_result = retrieve_textbook(args["query"])
            
            messages.append({
                "role": "assistant",
                "tool_calls": [tool_call]
            })
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })

        # Now stream the actual response
        stream = await client.chat.completions.create(
            model="mistralai/devstral-2512:free",
            messages=messages,
            temperature=0.3,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        print(f"ERROR - Agent Error: {e}")
        error_msg = f"Sorry, I encountered an error: {str(e)}" if language == "en" else f"معذرت، ایک خرابی واقع ہوئی: {str(e)}"
        yield f"data: {json.dumps({'type': 'content', 'data': error_msg})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

# ======================================================
# API ENDPOINTS
# ======================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "🤖 AI Tutor Backend with Streaming",
        "version": "2.1",
        "features": ["streaming", "multilingual"],
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/ (GET)"
        }
    }

@app.options("/chat")
async def chat_options():
    """Handle CORS preflight requests for /chat endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600"
        }
    )

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint with streaming support

    Request body:
    {
        "message": "Your question here",
        "language": "en" or "ur"
    }

    Returns: Server-Sent Events (SSE) stream
    """
    print(f"Received request - Message: {request.message[:50]}..., Language: {request.language}")

    return StreamingResponse(
        smart_agent_stream(request.message, request.language),  # 🔥 Pass language
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # Explicit CORS header for streaming
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "openai": "connected" if OPENROUTER_API_KEY else "missing",
        "cohere": "connected" if cohere_client else "not configured",
        "qdrant": "connected" if qdrant else "not configured"
    }

# ======================================================
# RUN SERVER
# ======================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🤖 AI TUTOR BACKEND STARTING...")
    print("="*50)
    print(f"✅ OpenAI: {'Connected' if OPENROUTER_API_KEY else '❌ Missing'}")
    print(f"✅ Cohere: {'Connected' if cohere_client else '⚠️ Not configured'}")
    print(f"✅ Qdrant: {'Connected' if qdrant else '⚠️ Not configured'}")
    print("🌐 Languages: English (en) | Urdu (ur)")
    print("="*50)
    print("🚀 Server running at: http://127.0.0.1:8000")
    print("📚 Docs available at: http://127.0.0.1:8000/docs")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)