"""
OpenAI Assistants helper for LightSignal
"""
import os
import time
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_assistant(assistant_id: str, user_text: str, timeout: int = 30) -> str:
    """
    Run an OpenAI assistant and return the text response.
    
    Args:
        assistant_id: The OpenAI assistant ID
        user_text: The user's question/prompt
        timeout: Max seconds to wait for completion
    
    Returns:
        The assistant's text response (concatenated from all text outputs)
    """
    if not assistant_id or not os.getenv("OPENAI_API_KEY"):
        return "Assistant unavailable."
    
    try:
        # Create thread
        thread = client.beta.threads.create()
        
        # Add user message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_text
        )
        
        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                # Get messages
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                
                # Concatenate all assistant text responses
                result_texts = []
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if hasattr(content, "text"):
                                result_texts.append(content.text.value)
                
                return "\n".join(result_texts) if result_texts else "No response"
            
            elif run_status.status in ["failed", "cancelled", "expired"]:
                return f"Assistant run {run_status.status}."
            
            # Wait before next poll
            time.sleep(1)
        
        return "Assistant timed out."
    
    except Exception as e:
        print(f"Assistant error: {e}")
        return "Assistant unavailable."