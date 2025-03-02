# InfraGPT

A CLI tool that converts natural language requests into Google Cloud (gcloud) commands.

## Installation

### From PyPI (Recommended)

Install directly from PyPI:

```
pip install infragpt
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

## Usage

### API Keys

InfraGPT requires API keys to work:

- For OpenAI GPT-4o: Set the `OPENAI_API_KEY` environment variable
- For Anthropic Claude: Set the `ANTHROPIC_API_KEY` environment variable

You can set these in your shell:
```
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

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

## Example Commands

- "Create a new GKE cluster with 3 nodes in us-central1"
- "List all storage buckets"
- "Create a Cloud SQL MySQL instance named 'mydb' in us-west1"
- "Set up a load balancer for my instance group 'web-servers'"

## Options

- `--model`, `-m`: Choose the LLM model (gpt4o or claude)
- `--verbose`, `-v`: Enable verbose output
