# InfraGPT

A CLI tool that converts natural language requests into Google Cloud (gcloud) commands.

![PyPI](https://img.shields.io/pypi/v/infragpt)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/priyanshujain/infragpt/publish.yml)

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

## Development

### Versioning and Releases

The project includes a helper script for versioning:

```bash
# Bump the patch version (0.1.0 -> 0.1.1)
./bump_version.py

# Bump the minor version (0.1.0 -> 0.2.0)
./bump_version.py minor

# Bump the major version (0.1.0 -> 1.0.0)
./bump_version.py major

# Bump and create a git commit and tag
./bump_version.py --commit
```

### CI/CD

This project uses GitHub Actions for CI/CD:

1. **Tests Workflow**: Runs on every PR and push to master
   - Installs the package
   - Verifies it can be imported
   - Checks package structure

2. **Publish Workflow**: Automatically publishes to PyPI
   - Triggers on pushes to the master branch
   - Requires PyPI secrets to be configured in GitHub

To set up PyPI publishing:
1. Create API tokens on PyPI
2. Add them as GitHub secrets:
   - `PYPI_USERNAME`: Your PyPI username
   - `PYPI_PASSWORD`: Your PyPI API token
