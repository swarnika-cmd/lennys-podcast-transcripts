import requests
from app.config import settings
from typing import List, Dict, Any, Optional

def get_ollama_embeddings(text: str) -> List[float]:
    url = f"{settings.ollama_url}/api/embeddings"
    payload = {
        "model": settings.ollama_embed_model,
        "prompt": text
    }
    resp = requests.post(url, json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json()["embedding"]

def get_openai_embeddings(text: str, api_key: str) -> List[float]:
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "text-embedding-3-small",
        "input": text
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

def get_embeddings(text: str, provider: str = "ollama") -> List[float]:
    if provider == "openai" and settings.openai_api_key:
        return get_openai_embeddings(text, settings.openai_api_key)
    # Default to Ollama embeddings
    return get_ollama_embeddings(text)

def chat_ollama(messages: List[Dict[str, str]]) -> str:
    url = f"{settings.ollama_url}/api/chat"
    payload = {
        "model": settings.ollama_chat_model,
        "messages": messages,
        "stream": False
    }
    resp = requests.post(url, json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json()["message"]["content"]

def chat_openai(messages: List[Dict[str, str]], api_key: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.openai_chat_model,
        "messages": messages
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def chat_anthropic(messages: List[Dict[str, str]], api_key: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    # Process system message
    system_prompt = ""
    filtered_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        else:
            filtered_messages.append(msg)
            
    payload = {
        "model": settings.anthropic_chat_model,
        "max_tokens": 4096,
        "messages": filtered_messages
    }
    if system_prompt:
        payload["system"] = system_prompt
        
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]

def chat_llm(messages: List[Dict[str, str]], provider: Optional[str] = None) -> str:
    prov = provider or settings.default_llm_provider
    if prov == "openai" and settings.openai_api_key:
        return chat_openai(messages, settings.openai_api_key)
    elif prov == "anthropic" and settings.anthropic_api_key:
        return chat_anthropic(messages, settings.anthropic_api_key)
    else:
        # Fallback to local Ollama
        return chat_ollama(messages)
