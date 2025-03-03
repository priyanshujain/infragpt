# InfraGPT

A CLI tool that converts natural language requests into Google Cloud (gcloud) commands.

![PyPI](https://img.shields.io/pypi/v/infragpt)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/priyanshujain/infragpt/publish.yml)

## Installation

### Using pip

Using pip to install packages system-wide is [not recommended](https://peps.python.org/pep-0668/). Instead, install InfraGPT using `pipx` in the next section.

### Using pipx

```
# Install pipx if you don't have it
pip install --user pipx
pipx ensurepath

# Install infragpt
pipx install infragpt
```

### From Source

1. Clone the repository:
   ```
   git clone https://github.com/priyanshujain/infragpt.git
   cd infragpt
   ```

2. Install in development mode:
   ```
   pip install -e .
   ```

## Credentials Management

InfraGPT requires API keys to work. There are three ways to provide credentials, in order of priority:

### 1. Command Line Parameters

```bash
# Using OpenAI GPT-4o
infragpt --model gpt4o --api-key "your-openai-api-key" "your prompt here"

# Using Anthropic Claude
infragpt --model claude --api-key "your-anthropic-api-key" "your prompt here"
```

### 2. Configuration File

InfraGPT stores credentials in `~/.config/infragpt/config.yaml` and uses them automatically on subsequent runs. This file is created:
- When you provide credentials interactively
- Automatically on first run if environment variables are available
- When you use command line parameters

### 3. Environment Variables

Set one or more of these environment variables:

```bash
# For OpenAI GPT-4o
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optionally specify the model
export INFRAGPT_MODEL="gpt4o"  # or "claude"
```

**Model Selection Rules**:
- If both API keys are set, InfraGPT uses OpenAI by default unless specified otherwise
- If only one API key is set, the corresponding model is used automatically
- If a model is explicitly selected (via command line or INFRAGPT_MODEL), the corresponding API key must be available

When environment variables are available, InfraGPT will automatically save the detected model and API key to the configuration file for future use.

If no credentials are found from any of these sources, if an empty API key is detected, or if an invalid API key is provided, InfraGPT will prompt you to select a model and enter your API key interactively at startup, before accepting any commands. 

**API Key Validation:**
- The application validates API keys by making a small test request to the service provider
- When entering credentials interactively, API keys are validated immediately
- Invalid keys from environment variables or the config file are detected at startup
- The system will continue prompting until valid credentials are provided
- All validated credentials are automatically saved to the config file

## Usage

### Command Line

Run InfraGPT directly with a prompt:

```
infragpt "create a new VM instance called test-vm in us-central1 with 2 CPUs"
```

Or specify the model to use:

```
infragpt --model claude "list all my compute instances in europe-west1"
```

### Interactive Mode

Launch InfraGPT in interactive mode (no initial prompt):

```
infragpt
```

Use keyboard shortcuts in interactive mode:
- `Ctrl+D` to exit the application
- `Ctrl+C` to clear the current input and start a new prompt

## Example Commands

- "Create a new GKE cluster with 3 nodes in us-central1"
- "List all storage buckets"
- "Create a Cloud SQL MySQL instance named 'mydb' in us-west1"
- "Set up a load balancer for my instance group 'web-servers'"

## Options

- `--model`, `-m`: Choose the LLM model (gpt4o or claude)
- `--api-key`, `-k`: Provide an API key for the selected model
- `--verbose`, `-v`: Enable verbose output

## Contributing

For information on how to contribute to InfraGPT, including development setup, release process, and CI/CD configuration, please see the [CONTRIBUTING.md](CONTRIBUTING.md) file.