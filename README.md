<div align="center">
<pre>
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                    │
│  ██╗   ██╗ ██████╗███████╗    ██╗      ██████╗  ██████╗        ██████╗██╗     ██╗  │
│  ██║   ██║██╔════╝██╔════╝    ██║     ██╔═══██╗██╔════╝       ██╔════╝██║     ██║  │
│  ██║   ██║██║     █████╗█████╗██║     ██║   ██║██║  ███╗█████╗██║     ██║     ██║  │
│  ╚██╗ ██╔╝██║     ██╔══╝╚════╝██║     ██║   ██║██║   ██║╚════╝██║     ██║     ██║  │
│   ╚████╔╝ ╚██████╗██║         ███████╗╚██████╔╝╚██████╔╝      ╚██████╗███████╗██║  │
│    ╚═══╝   ╚═════╝╚═╝         ╚══════╝ ╚═════╝  ╚═════╝        ╚═════╝╚══════╝╚═╝  │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
</pre>
</div>
<div align="center">

<h3>CLI utility for Analyze and Parse SDDC Manager SoS Log Bundles</h3>
<br>
</div>

<div align="center">
    <img src="https://img.shields.io/badge/status-stable-green"/>
    <img src="https://img.shields.io/badge/development-active-green"/> <br>
    <img src="https://img.shields.io/badge/version-2.0.3-blue"/>
    <br>
    <br>
</div>

<div align="center"">
    ___________________________________________________
    <br>
</div>

## Details

`vcf_log_cli` for VCF is a python based log parsing tool that runs against an SOS bundle collected from SDDC Manager.

With the complexity and vast scope of the information present in an SOS bundle, the objective here is to reduce some of this complexity and scope, by parsing through a lot of the information and presenting it on a smaller scale that is easier to digest.
Additionally, the objective is to also present much of the environmental information in one place, and thereby reduce the number of TSE hours spent manually searching for the same information across multiple files.

## Installation

There are several ways to install `vcf_log_cli` depending on your preference and environment:

### Method 1: Install from wheel distribution
Download the wheel file from the `dist` directory and install:
```bash
pip install dist/vcf_log_cli-2.0.3-py3-none-any.whl
```

### Method 2: Install from source distribution
Download the source distribution from the `dist` directory and install:
```bash
pip install dist/vcf_log_cli-2.0.3.tar.gz
```

### Method 3: Install with Poetry
If you prefer to use Poetry for dependency management:
```bash
# Clone the repository
git clone <repository-url>
cd vcf_log_cli

# Install dependencies and package
poetry install
```

### Method 4: Install with pip in editable mode
For development purposes, you can install in editable mode:
```bash
pip install -e .
```

### Method 5: Install with uv (Modern Python package installer)
If you're using uv for faster package installation:
```bash
uv pip install dist/vcf_log_cli-2.0.3-py3-none-any.whl
```

### Prerequisites
- Python 3.9 or higher
- Required dependencies will be automatically installed:
  - typer (>=0.12.3)
  - simple-term-menu (>=1.6.4)
  - tabview (>=1.4.4)
  - pyyaml (>=6.0.1)

After installation, you can run the tool using:
```bash
vcf_log_cli --help
```


## Usage

After installation, you can run `vcf_log_cli` from any directory where you have an SDDC Manager SOS bundle extracted.

### General Help
```bash
vcf_log_cli --help
```

### Command: parselogs
Parses SDDC Manager log files to create consolidated `.all` files and optionally `.error` files for services.

```bash
vcf_log_cli parselogs [OPTIONS]
```

**Options:**
- `--errorfiles`: Generates `.error` files for services by aggregating ERROR messages across multiple log files. This process can take several minutes to complete.

**Description:**
This command creates a `results_file.txt` and `.all` files for all services. The `.all` files contain consolidated logs from the latest 10 log files for each service. If the `--errorfiles` flag is used, it also generates `.error` files that contain filtered ERROR messages with known false positives removed.

**Services Processed:**
- lcm (Lifecycle Manager)
- domainmanager
- commonsvcs
- operationsmanager
- sddc-manager-ui-app

**Example Usage:**
```bash
# Basic usage - creates .all files and results file
vcf_log_cli parselogs

# With error file generation
vcf_log_cli parselogs --errorfiles
```

### Command: upgradehelper
Runs an offline version of the upgrade helper tool to analyze bundle availability and version aliasing.

```bash
vcf_log_cli upgradehelper
```

**Description:**
This command performs several checks to assist with VCF upgrades:
- Checks if Async Patching is enabled
- Verifies LCM Manifest Polling status
- Identifies SDDC Manager version
- Lists all VCF domains for selection
- Checks status of required upgrade bundles
- Verifies current component versions (NSX-T, vCenter, ESXi)
- Performs version alias detection and validation

**Example Usage:**
```bash
vcf_log_cli upgradehelper
```

### Command: database
Runs a visual Database Table Navigator to explore database dumps.

```bash
vcf_log_cli database [OPTIONS]
```

**Options:**
- `--recreate`: Scans the DB dump and re-creates the DB files and directories.

**Description:**
This command parses the `postgres-db-dump` or `postgres-db-dump.gz` file and creates organized files for each database table. It then provides an interactive terminal menu to navigate and view the database tables.

**Example Usage:**
```bash
# Initial run - creates DB files and starts navigator
vcf_log_cli database

# Re-create DB files if they already exist
vcf_log_cli database --recreate
```

### Command: workflow
Collects subtask details for a given workflow ID.

```bash
vcf_log_cli workflow [OPTIONS]
```

**Options:**
- `--id TEXT`: ID of the workflow identified from the results file [required]
- `--as-file`: Generates a file with all sub-task details for a given workflow ID
- `--help`: Show help message and exit

**Description:**
This command retrieves detailed subtask information for a specific workflow ID from the database. It searches in both the domainmanager and opsmgr databases for processing context entries matching the provided workflow ID.

**Example Usage:**
```bash
# Display workflow subtasks in terminal
vcf_log_cli workflow --id WORKFLOW_ID

# Generate a file with workflow subtask details
vcf_log_cli workflow --as-file --id WORKFLOW_ID
```

## Output Files

When running `vcf_log_cli`, the following files are generated in the `vcf_log_cli` directory:
- `results_file.txt`: Contains environment summary, service statuses, domain information, and recent workflows
- `SERVICE.all`: Consolidated log files for each service (latest 10 log files)
- `SERVICE.error`: Filtered ERROR messages for each service (when using --errorfiles flag)

When using the database command, files are generated in the `vcf_log_cli_db` directory, organized by database name and containing tab-separated values for each table.


## Support
For any questions and concerns, please reach out to Laraib Kazi or create a Github issue.

