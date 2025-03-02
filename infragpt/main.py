#!/usr/bin/env python3

import os
import sys
import argparse
import json
from typing import Literal, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

MODEL_TYPE = Literal["gpt4o", "claude"]

def setup_parser() -> argparse.ArgumentParser:
    """Set up command line arguments parser."""
    parser = argparse.ArgumentParser(description="InfraGPT - Cloud infrastructure command generator")
    parser.add_argument("prompt", nargs="*", help="Natural language prompt for cloud operation")
    parser.add_argument("--model", "-m", type=str, choices=["gpt4o", "claude"], default="gpt4o",
                        help="LLM model to use (default: gpt4o)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    return parser

def get_llm(model_type: MODEL_TYPE, verbose: bool = False):
    """Initialize the appropriate LLM based on user selection."""
    if model_type == "gpt4o":
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY environment variable not set.")
            sys.exit(1)
        return ChatOpenAI(model="gpt-4o", temperature=0)
    elif model_type == "claude":
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY environment variable not set.")
            sys.exit(1)
        return ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")

def create_prompt():
    """Create the prompt template for generating cloud commands."""
    template = """You are InfraGPT, a specialized assistant that helps users convert their natural language requests into 
appropriate Google Cloud (gcloud) CLI commands.

INSTRUCTIONS:
1. Analyze the user's input to understand the intended cloud operation.
2. If the request is valid and related to Google Cloud operations, respond with ONLY the appropriate gcloud command.
3. If the user input is invalid, unclear, or not related to Google Cloud operations, respond with exactly: "Request cannot be fulfilled."
4. Do not include any explanations, markdown formatting, or additional text in your response.

Examples:
- Request: "Create a new VM instance called test-instance with 2 CPUs in us-central1-a"
  Response: gcloud compute instances create test-instance --machine-type=e2-medium --zone=us-central1-a
  
- Request: "What's the weather like today?"
  Response: Request cannot be fulfilled.

User request: {prompt}

Your gcloud command:"""
    
    return ChatPromptTemplate.from_template(template)

def generate_gcloud_command(prompt: str, model_type: MODEL_TYPE, verbose: bool = False) -> str:
    """Generate a gcloud command based on the user's natural language prompt."""
    # Initialize the LLM
    llm = get_llm(model_type, verbose)
    
    # Create the prompt
    prompt_template = create_prompt()
    
    # Create and execute the chain
    chain = prompt_template | llm | StrOutputParser()
    result = chain.invoke({"prompt": prompt})
    
    return result.strip()

def main():
    parser = setup_parser()
    args = parser.parse_args()
    
    # If no prompt was provided, enter interactive mode
    if not args.prompt:
        print("InfraGPT (Ctrl+C to exit)")
        print(f"Using model: {args.model}")
        try:
            while True:
                user_input = input("\nEnter your cloud operation request: ")
                if not user_input.strip():
                    continue
                result = generate_gcloud_command(user_input, args.model, args.verbose)
                print(f"\n{result}")
        except KeyboardInterrupt:
            print("\nExiting InfraGPT.")
            sys.exit(0)
    else:
        prompt = " ".join(args.prompt)
        result = generate_gcloud_command(prompt, args.model, args.verbose)
        print(result)

if __name__ == "__main__":
    main()