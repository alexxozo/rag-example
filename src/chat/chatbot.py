import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from langfuse import Langfuse
from src.core.config import settings
from src.retrieval.vector_store import VectorStore


class RAGChatbot:
    def __init__(self):
        self.vector_store = VectorStore()
        self.logger = logging.getLogger(__name__)
        
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.openai_client = None
        
        # Initialize Langfuse only if credentials are provided
        if (settings.langfuse_public_key and 
            settings.langfuse_secret_key and 
            settings.langfuse_public_key.strip() and 
            settings.langfuse_secret_key.strip()):
            try:
                self.langfuse = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host
                )
                self.logger.info("Langfuse observability enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Langfuse: {e}")
                self.langfuse = None
        else:
            self.langfuse = None
            self.logger.info("Langfuse observability disabled")
        
        self.conversation_history: List[Dict[str, str]] = []

    def chat(self, user_message: str, session_id: Optional[str] = None) -> str:
        try:
            if self.langfuse:
                trace = self.langfuse.trace(
                    name="rag_chat",
                    session_id=session_id or "default",
                    input={"user_message": user_message}
                )
            else:
                trace = None
            
            relevant_docs = self.vector_store.search(
                query=user_message,
                limit=5,
                score_threshold=0.3
            )
            
            if trace:
                trace.span(
                    name="retrieval",
                    input={"query": user_message},
                    output={"retrieved_docs_count": len(relevant_docs)}
                )
            
            context = self._build_context(relevant_docs)
            
            prompt = self._build_prompt(user_message, context)
            
            response = self._generate_response(prompt, trace)
            
            self.conversation_history.append({
                "user": user_message,
                "assistant": response
            })
            
            if trace:
                trace.update(output={"response": response})
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            return "I'm sorry, I encountered an error while processing your question. Please try again."

    def _build_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        if not relevant_docs:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            source = doc["metadata"].get("source", "Unknown")
            content = doc["content"]
            score = doc["score"]
            
            context_parts.append(
                f"Document {i} (Source: {source}, Relevance: {score:.3f}):\n{content}\n"
            )
        
        return "\n".join(context_parts)

    def _build_prompt(self, user_message: str, context: str) -> str:
        conversation_context = ""
        if self.conversation_history:
            recent_history = self.conversation_history[-3:]
            for exchange in recent_history:
                conversation_context += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
        
        prompt = f"""You are a helpful AI assistant that answers questions based on the provided documents. 
Use the context below to answer the user's question. If the answer is not in the provided context, 
say so clearly and provide general guidance if possible.

Previous conversation:
{conversation_context}

Relevant documents:
{context}

User question: {user_message}

Please provide a helpful and accurate answer based on the available information:"""
        
        return prompt

    def _generate_response(self, prompt: str, trace=None) -> str:
        try:
            if settings.llm_provider == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                if trace:
                    trace.generation(
                        name="openai_chat",
                        model="gpt-3.5-turbo",
                        input=prompt,
                        output=response.choices[0].message.content,
                        usage={
                            "promptTokens": response.usage.prompt_tokens,
                            "completionTokens": response.usage.completion_tokens,
                            "totalTokens": response.usage.total_tokens
                        }
                    )
                
                return response.choices[0].message.content.strip()
            
            else:
                return "OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file."
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"I encountered an error while generating a response: {str(e)}"

    def clear_history(self):
        self.conversation_history = []
        self.logger.info("Cleared conversation history")

    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation_history.copy()