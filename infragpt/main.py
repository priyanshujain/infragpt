#!/usr/bin/env python3

import os
import sys
import re
from typing import Literal, Optional, List, Dict, Tuple, Any

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
import pathlib

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize console for rich output
console = Console()

# Define type for model selection
MODEL_TYPE = Literal["gpt4o", "claude"]

def get_llm(model_type: MODEL_TYPE, verbose: bool = False):
    """Initialize the appropriate LLM based on user selection."""
    if model_type == "gpt4o":
        if not os.getenv("OPENAI_API_KEY"):
            console.print("[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set.")
            sys.exit(1)
        return ChatOpenAI(model="gpt-4o", temperature=0)
    elif model_type == "claude":
        if not os.getenv("ANTHROPIC_API_KEY"):
            console.print("[bold red]Error:[/bold red] ANTHROPIC_API_KEY environment variable not set.")
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
2. If the request is valid and related to Google Cloud operations, respond with ONLY the appropriate gcloud command(s).
3. If the operation requires multiple commands, separate them with a newline.
4. Include parameter placeholders in square brackets like [PROJECT_ID], [TOPIC_NAME], [SUBSCRIPTION_NAME], etc.
5. Do not include any explanations, markdown formatting, or additional text in your response.

Examples:
- Request: "Create a new VM instance called test-instance with 2 CPUs in us-central1-a"
  Response: gcloud compute instances create test-instance --machine-type=e2-medium --zone=us-central1-a

- Request: "Give viewer permissions to user@example.com for a pubsub topic"
  Response: gcloud pubsub topics add-iam-policy-binding [TOPIC_NAME] --member=user:user@example.com --role=roles/pubsub.viewer

- Request: "Create a VM instance and attach a new disk to it"
  Response: gcloud compute instances create [INSTANCE_NAME] --zone=[ZONE] --machine-type=e2-medium
gcloud compute disks create [DISK_NAME] --size=200GB --zone=[ZONE]
gcloud compute instances attach-disk [INSTANCE_NAME] --disk=[DISK_NAME] --zone=[ZONE]

- Request: "What's the weather like today?"
  Response: Request cannot be fulfilled.

User request: {prompt}

Your gcloud command(s):"""
    
    return ChatPromptTemplate.from_template(template)

def create_parameter_prompt():
    """Create prompt template for extracting parameter info from a command."""
    template = """You are InfraGPT Parameter Helper, a specialized assistant that helps users understand Google Cloud CLI command parameters.

TASK:
Analyze the Google Cloud CLI command below and provide information about each parameter that needs to be filled in.
For each parameter in square brackets like [PARAMETER_NAME], provide:
1. A brief description of what this parameter is
2. Examples of valid values
3. Any constraints or requirements

Format your response as JSON with the parameter name as key, like this:
```json
{{
  "PARAMETER_NAME": {{
    "description": "Brief description of the parameter",
    "examples": ["example1", "example2"], 
    "required": true,
    "default": "default value if any, otherwise null"
  }}
}}
```

Command: {command}

Parameter JSON:"""
    
    return ChatPromptTemplate.from_template(template)

def get_parameter_info(command: str, model_type: MODEL_TYPE) -> Dict[str, Dict[str, Any]]:
    """Get information about parameters from the LLM."""
    # Extract parameters that need filling in (those in square brackets)
    bracket_params = re.findall(r'\[([A-Z_]+)\]', command)
    
    if not bracket_params:
        return {}
    
    # Create a prompt to get parameter info
    llm = get_llm(model_type)
    prompt_template = create_parameter_prompt()
    
    # Create and execute the chain
    chain = prompt_template | llm | StrOutputParser()
    
    with console.status("[bold blue]Analyzing command parameters...[/bold blue]", spinner="dots"):
        result = chain.invoke({"command": command})
    
    # Extract the JSON part
    try:
        import json
        # Find JSON part between triple backticks if present
        if "```json" in result:
            json_part = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            json_part = result.split("```")[1].strip()
        else:
            json_part = result.strip()
        
        parameter_info = json.loads(json_part)
        return parameter_info
    except Exception as e:
        console.print(f"[bold yellow]Warning:[/bold yellow] Could not parse parameter info: {e}")
        return {}

def parse_command_parameters(command: str) -> Tuple[str, Dict[str, str], List[str]]:
    """Parse a command to extract its parameters and bracket placeholders."""
    # Extract base command and arguments
    parts = command.split()
    base_command = []
    
    params = {}
    current_param = None
    bracket_params = []
    
    for part in parts:
        # Extract parameters in square brackets (could be in any part of the command)
        bracket_matches = re.findall(r'\[([A-Z_]+)\]', part)
        if bracket_matches:
            for match in bracket_matches:
                bracket_params.append(match)
            
        if part.startswith('--'):
            # Handle --param=value format
            if '=' in part:
                param_name, param_value = part.split('=', 1)
                params[param_name[2:]] = param_value
            else:
                current_param = part[2:]
                params[current_param] = None
        elif current_param is not None:
            # This is a value for the previous parameter
            params[current_param] = part
            current_param = None
        else:
            # This is part of the base command
            base_command.append(part)
    
    return ' '.join(base_command), params, bracket_params

def prompt_for_parameters(command: str, model_type: MODEL_TYPE) -> str:
    """Prompt the user for each parameter in the command with AI assistance."""
    # Show the original command template first
    console.print("\n[bold blue]Command template:[/bold blue]")
    console.print(Panel(command, border_style="blue"))

    # Parse command to get base command, existing params, and placeholder params
    base_command, params, bracket_params = parse_command_parameters(command)
    
    # If command contains bracket params, get parameter info from LLM
    parameter_info = {}
    if bracket_params:
        parameter_info = get_parameter_info(command, model_type)
    
    # If no parameters of any kind, just return the command as is
    if not params and not bracket_params:
        return command
    
    # First handle bracket parameters with a separate section
    if bracket_params:
        console.print("\n[bold magenta]Command requires the following parameters:[/bold magenta]")
        
        # Replace bracket parameters in base command and all params
        command_with_replacements = command
        
        for param in bracket_params:
            info = parameter_info.get(param, {})
            description = info.get('description', f"Value for {param}")
            examples = info.get('examples', [])
            default = info.get('default', None)
            
            # Create a rich prompt with available info
            prompt_text = f"[bold cyan]{param}[/bold cyan]"
            if description:
                prompt_text += f"\n  [dim]{description}[/dim]"
            if examples:
                examples_str = ", ".join([str(ex) for ex in examples])
                prompt_text += f"\n  [dim]Examples: {examples_str}[/dim]"
                
            # Get user input for this parameter
            value = Prompt.ask(prompt_text, default=default or "")
            
            # Replace all occurrences of [PARAM] with the value
            command_with_replacements = command_with_replacements.replace(f"[{param}]", value)
        
        # Now we have a command with all bracket params replaced
        return command_with_replacements
    
    # If we just have regular parameters (no brackets), handle them normally
    console.print("\n[bold yellow]Command parameters:[/bold yellow]")
    
    # Prompt for each parameter
    updated_params = {}
    for param, default_value in params.items():
        prompt_text = f"[bold cyan]{param}[/bold cyan]"
        if default_value:
            prompt_text += f" [default: {default_value}]"
        
        value = Prompt.ask(prompt_text, default=default_value or "")
        updated_params[param] = value
    
    # Reconstruct command
    reconstructed_command = base_command
    for param, value in updated_params.items():
        if value:  # Only add non-empty parameters
            reconstructed_command += f" --{param}={value}"
    
    return reconstructed_command

def split_commands(result: str) -> List[str]:
    """Split multiple commands from the response."""
    if "Request cannot be fulfilled." in result:
        return [result]
    
    # Split by newlines and filter out empty lines
    commands = [cmd.strip() for cmd in result.splitlines() if cmd.strip()]
    return commands

def handle_command_result(result: str, model_type: MODEL_TYPE, verbose: bool = False):
    """Handle the generated command results with options to print, copy, or execute."""
    commands = split_commands(result)
    
    if not commands:
        console.print("[bold red]No valid commands generated[/bold red]")
        return
    
    # If it's an error response, just display it
    if commands[0] == "Request cannot be fulfilled.":
        console.print(f"[bold red]{commands[0]}[/bold red]")
        return
    
    # Show the number of commands if multiple
    if len(commands) > 1:
        console.print(f"\n[bold blue]Generated {len(commands)} commands:[/bold blue]")
        for i, cmd in enumerate(commands):
            console.print(f"[dim]{i+1}.[/dim] [italic]{cmd.split()[0]}...[/italic]")
        console.print()
    
    # Process each command
    processed_commands = []
    for i, command in enumerate(commands):
        if verbose or len(commands) > 1:
            console.print(f"\n[bold cyan]Command {i+1} of {len(commands)}:[/bold cyan]")
            
        # Check if command has parameters and prompt for them
        if '[' in command or '--' in command:
            processed_command = prompt_for_parameters(command, model_type)
            processed_commands.append(processed_command)
            console.print(Panel(processed_command, border_style="green", title=f"Final Command {i+1}"))
        else:
            processed_commands.append(command)
            console.print(Panel(command, border_style="green", title=f"Command {i+1}"))
    
    # Set choices to just copy and run, with copy as default
    choices = []
    if CLIPBOARD_AVAILABLE:
        choices.append("copy")
    choices.append("run")
    
    # If nothing is available, add print option
    if not choices:
        choices.append("print")
    
    # Default to copy if available, otherwise first option
    default = "copy" if CLIPBOARD_AVAILABLE else choices[0]
    
    # For each command, ask what to do
    for i, command in enumerate(processed_commands):
        if len(commands) > 1:
            console.print(f"\n[bold cyan]Action for command {i+1}:[/bold cyan]")
            console.print(Panel(command, border_style="blue"))
        
        # Use rich to display options and get choice
        choice = Prompt.ask(
            "[bold yellow]What would you like to do with this command?[/bold yellow]",
            choices=choices,
            default=default
        )
        
        if choice == "copy" and CLIPBOARD_AVAILABLE:
            try:
                pyperclip.copy(command)
                console.print("[bold green]Command copied to clipboard![/bold green]")
            except Exception as e:
                console.print(f"[bold red]Failed to copy to clipboard: {e}[/bold red]")
                console.print("[dim]You can manually copy the command above.[/dim]")
        elif choice == "run":
            console.print("\n[bold yellow]Executing command...[/bold yellow]")
            try:
                os.system(command)
            except Exception as e:
                console.print(f"[bold red]Error executing command: {e}[/bold red]")
            
            if i < len(processed_commands) - 1:
                # Ask if they want to continue with the next command
                if not Confirm.ask("[bold yellow]Continue with the next command?[/bold yellow]", default=True):
                    break

def generate_gcloud_command(prompt: str, model_type: MODEL_TYPE, verbose: bool = False) -> str:
    """Generate a gcloud command based on the user's natural language prompt."""
    # Initialize the LLM
    llm = get_llm(model_type, verbose)
    
    if verbose:
        console.print(f"[dim]Generating command using {model_type}...[/dim]")
    
    # Create the prompt
    prompt_template = create_prompt()
    
    # Create and execute the chain
    chain = prompt_template | llm | StrOutputParser()
    result = chain.invoke({"prompt": prompt})
    
    return result.strip()

def interactive_mode(model_type: MODEL_TYPE, verbose: bool = False):
    """Run InfraGPT in interactive mode with enhanced prompting."""
    # Ensure history directory exists
    history_dir = pathlib.Path.home() / ".infragpt"
    history_dir.mkdir(exist_ok=True)
    history_file = history_dir / "history"
    
    # Setup prompt toolkit session with history
    session = PromptSession(history=FileHistory(str(history_file)))
    
    # Style for prompt
    style = Style.from_dict({
        'prompt': '#00FFFF bold',
    })
    
    # Welcome message
    console.print(Panel.fit(
        Text("InfraGPT - Convert natural language to gcloud commands", style="bold green"),
        border_style="blue"
    ))
    console.print(f"[yellow]Using model:[/yellow] [bold]{model_type}[/bold]")
    console.print("[dim]Press Ctrl+D to exit, Ctrl+C to clear input[/dim]\n")
    
    while True:
        try:
            # Get user input with prompt toolkit
            user_input = session.prompt(
                [('class:prompt', '> ')], 
                style=style,
                multiline=False
            )
            
            if not user_input.strip():
                continue
                
            with console.status("[bold green]Generating command...[/bold green]", spinner="dots"):
                result = generate_gcloud_command(user_input, model_type, verbose)
            
            handle_command_result(result, model_type, verbose)
        except KeyboardInterrupt:
            # Clear the current line and show a new prompt
            console.print("\n[yellow]Input cleared. Enter a new prompt:[/yellow]")
            continue
        except EOFError:
            # Exit on Ctrl+D
            console.print("\n[bold]Exiting InfraGPT.[/bold]")
            sys.exit(0)

@click.command()
@click.argument('prompt', nargs=-1)
@click.option('--model', '-m', type=click.Choice(['gpt4o', 'claude']), default='gpt4o', 
              help='LLM model to use')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.version_option(package_name='infragpt')
def main(prompt, model, verbose):
    """InfraGPT - Convert natural language to Google Cloud commands."""
    if verbose:
        from importlib.metadata import version
        try:
            console.print(f"[dim]InfraGPT version: {version('infragpt')}[/dim]")
        except:
            console.print("[dim]InfraGPT: Version information not available[/dim]")
    
    # If no prompt was provided, enter interactive mode
    if not prompt:
        interactive_mode(model, verbose)
    else:
        user_prompt = " ".join(prompt)
        with console.status("[bold green]Generating command...[/bold green]", spinner="dots"):
            result = generate_gcloud_command(user_prompt, model, verbose)
        
        handle_command_result(result, model, verbose)

if __name__ == "__main__":
    main()