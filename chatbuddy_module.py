# ---------------------------------------------------
# Version: 14.07.2024
# Author: M. Weber
# ---------------------------------------------------
# 
# ---------------------------------------------------

from datetime import datetime
import os
from dotenv import load_dotenv

# from pymongo import MongoClient
# from pymongo.errors import DuplicateKeyError

import openai
import anthropic
from groq import Groq
import ollama

from duckduckgo_search import DDGS
from tavily import TavilyClient

import torch
# from transformers import AutoTokenizer, AutoModel
from transformers import BertTokenizer, BertModel

# Define global variables ----------------------------------
LLMS = ("openai_gpt-4o", "anthropic", "groq_mixtral-8x7b-32768", "groq_llama3-70b-8192", "groq_gemma-7b-it")

# Init MongoDB Client
load_dotenv()
# mongoClient = MongoClient(os.environ.get('MONGO_URI_DVV'))
# database = mongoClient.chatbuddy
# collection = database.dvv_artikel
# collection_config = database.config
openaiClient = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY_DVV'))
anthropicClient = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY_DVV'))
groqClient = Groq(api_key=os.environ['GROQ_API_KEY_PRIVAT'])
tavilyClient = TavilyClient(api_key=os.environ['TAVILY_API_KEY_DVV'])

# Load pre-trained model and tokenizer
os.environ["TOKENIZERS_PARALLELISM"] = "false"
model_name = "bert-base-german-cased" # 768 dimensions
# model_name = "bert-base-multilingual-cased"
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)

# Define Database functions ----------------------------------
def ask_llm(llm: str, temperature: float = 0.2, question: str = "", history: list = [],
            systemPrompt: str = "", db_results_str: str = "", web_results_str: str = "") -> str:
    # define prompt
    datum_context = f" Heute ist der {str(datetime.now().date())}."
    input_messages = \
        [{"role": "system", "content": systemPrompt + datum_context}] \
        + history \
        + [{"role": "user", "content": question}]
    if llm == "openai_gpt-4o":
        response = openaiClient.chat.completions.create(
            model="gpt-4o",
            temperature=temperature,
            messages=input_messages
            )
        output = response.choices[0].message.content
    elif llm == "anthropic":
        response = anthropicClient.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system=systemPrompt,
            messages=input_messages[1:] # system prompt is not needed
        )
        output = response.content[0].text
    elif llm == "groq_mixtral-8x7b-32768":
        response = groqClient.chat.completions.create(
            model="mixtral-8x7b-32768",
            temperature=temperature,
            messages=input_messages
        )
        output = response.choices[0].message.content
    elif llm == "groq_llama3-70b-8192":
        response = groqClient.chat.completions.create(
            model="llama3-70b-8192",
            temperature=temperature,
            messages=input_messages
        )
        output = response.choices[0].message.content
    elif llm == "groq_gemma-7b-it":
        response = groqClient.chat.completions.create(
            model="gemma-7b-it",
            temperature=temperature,
            messages=input_messages
        )
        output = response.choices[0].message.content
    elif llm == "ollama_mistral":
        response = ollama.chat(model="mistral", messages=input_messages)
        output = response['message']['content']
    elif llm == "ollama_llama3":
        response = ollama.chat(model="llama3", messages=input_messages)
        output = response['message']['content']
    else:
        output = "Error: No valid LLM specified."
    return output

def web_search_ddgs(query: str = "", limit: int = 10) -> list:
    # results = DDGS().text(f"Nachrichten über '{query}'", max_results=limit)
    results = DDGS().news(query, max_results=limit)
    return results if results else []

def web_search_tavily(query: str = "", score: float = 0.5, limit: int = 10) -> list:
    results: list = []
    results_list = tavilyClient.search(query=query, max_results=limit, include_raw_content=True)
    for result in results_list['results']:
        if result['score'] > score:
            results.append(result)
    return results

def print_results(cursor: list) -> None:
    if not cursor:
        print("Keine Artikel gefunden.")
    for item in cursor:
        print(f"[{str(item['datum'])[:10]}] {item['titel'][:70]}")
    
