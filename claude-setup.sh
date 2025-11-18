#!/bin/bash

################################################################################
# Claude Code Complete Setup Script - All-in-One Edition
# This script sets up a complete Claude Code installation with all MCPs,
# plugins, and agents in a single execution.
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_section() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    exit 1
fi

print_section "Claude Code Complete Installation"
print_status "This script will install:"
print_status "  • Claude Code CLI"
print_status "  • 2 Plugin Marketplaces (100+ plugins)"
print_status "  • 8 MCP Servers (including Playwright)"
print_status "  • Development environment setup"
echo ""

################################################################################
# 1. Install Claude Code CLI
################################################################################
print_section "Step 1/7: Installing Claude Code CLI"

if ! command -v node &> /dev/null; then
    print_status "Node.js not found. Installing Node.js via nvm..."

    # Install NVM
    if [ ! -d "$HOME/.nvm" ]; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    fi

    # Install Node.js LTS
    nvm install --lts
    nvm use --lts
    print_status "✓ Node.js installed: $(node --version)"
else
    print_status "✓ Node.js already installed: $(node --version)"
fi

# Install Claude Code globally
if ! command -v claude &> /dev/null; then
    print_status "Installing @anthropic-ai/claude-code..."
    sudo npm install -g @anthropic-ai/claude-code
    print_status "✓ Claude Code CLI installed"
else
    print_status "✓ Claude Code CLI already installed"
    print_warning "Updating to latest version..."
    sudo npm update -g @anthropic-ai/claude-code
fi

################################################################################
# 2. Install UV (for Python-based MCP servers)
################################################################################
print_section "Step 2/7: Installing UV for Python MCP Servers"

if ! command -v uvx &> /dev/null; then
    print_status "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    print_status "✓ UV installed"
else
    print_status "✓ UV already installed"
fi

################################################################################
# 3. Create Claude configuration directory structure
################################################################################
print_section "Step 3/7: Creating Configuration Directories"

print_status "Creating Claude configuration structure..."
mkdir -p ~/.claude/{plugins/marketplaces,session-env,shell-snapshots,statsig,projects,todos,debug}
print_status "✓ Directory structure created"

################################################################################
# 4. Install Plugin Marketplaces
################################################################################
print_section "Step 4/7: Installing Plugin Marketplaces"

# Marketplace 1: claude-code-workflows (wshobson/agents)
print_status "[1/2] Installing claude-code-workflows (64+ plugins, 87+ agents)..."
PLUGIN_DIR_1="$HOME/.claude/plugins/marketplaces/claude-code-workflows"

if [ ! -d "$PLUGIN_DIR_1" ]; then
    git clone --depth 1 https://github.com/wshobson/agents "$PLUGIN_DIR_1"
    print_status "✓ claude-code-workflows installed"
else
    print_status "✓ claude-code-workflows exists, updating..."
    cd "$PLUGIN_DIR_1" && git pull && cd - > /dev/null 2>&1
fi

# Marketplace 2: claude-code-marketplace (ananddtyagi)
print_status "[2/2] Installing claude-code-marketplace (community plugins)..."
PLUGIN_DIR_2="$HOME/.claude/plugins/marketplaces/claude-code-marketplace"

if [ ! -d "$PLUGIN_DIR_2" ]; then
    git clone --depth 1 https://github.com/ananddtyagi/claude-code-marketplace "$PLUGIN_DIR_2"
    print_status "✓ claude-code-marketplace installed"
else
    print_status "✓ claude-code-marketplace exists, updating..."
    cd "$PLUGIN_DIR_2" && git pull && cd - > /dev/null 2>&1
fi

# Create plugin marketplace registry
print_status "Creating marketplace registry..."
cat > ~/.claude/plugins/known_marketplaces.json <<EOF
{
  "claude-code-workflows": {
    "source": {
      "source": "github",
      "repo": "wshobson/agents"
    },
    "installLocation": "$HOME/.claude/plugins/marketplaces/claude-code-workflows",
    "lastUpdated": "$(date -Iseconds)"
  },
  "claude-code-marketplace": {
    "source": {
      "source": "github",
      "repo": "ananddtyagi/claude-code-marketplace"
    },
    "installLocation": "$HOME/.claude/plugins/marketplaces/claude-code-marketplace",
    "lastUpdated": "$(date -Iseconds)"
  }
}
EOF

print_status "✓ Plugin marketplaces configured"

################################################################################
# 5. Configure Claude Code Settings
################################################################################
print_section "Step 5/7: Configuring Claude Code Settings"

print_status "Creating settings.json..."
cat > ~/.claude/settings.json <<'EOF'
{
  "enabledPlugins": {
    "backend-development@claude-code-workflows": true
  }
}
EOF

print_status "Creating settings.local.json with permissions..."
cat > ~/.claude/settings.local.json <<'EOF'
{
  "permissions": {
    "allow": [
      "Bash(sudo apt update:*)",
      "Bash(sudo apt upgrade:*)",
      "Bash(sudo apt install:*)",
      "Bash(wget:*)",
      "Bash(sudo tee:*)",
      "Bash(curl:*)",
      "Bash(bash)",
      "Bash(export NVM_DIR=\"$HOME/.nvm\")",
      "Bash([ -s \"$NVM_DIR/nvm.sh\" ])",
      "Bash(. \"$NVM_DIR/nvm.sh\")",
      "Bash(nvm install:*)",
      "Bash(node --version:*)",
      "Bash(npm --version)",
      "Bash(npm install:*)",
      "Bash(export PYENV_ROOT=\"$HOME/.pyenv\")",
      "Bash([[ -d $PYENV_ROOT/bin ]])",
      "Bash(export PATH=\"$PYENV_ROOT/bin:$PATH\")",
      "Bash(pyenv install:*)",
      "Bash(pyenv global:*)",
      "Bash(pip --version:*)",
      "Bash(pip install:*)",
      "Bash(sh -s -- -y)",
      "Bash(sudo snap install:*)",
      "Read(//tmp/**)",
      "Bash(code --install-extension:*)",
      "Bash(code --no-sandbox --user-data-dir=/root/.vscode-root --install-extension dbaeumer.vscode-eslint --force)",
      "Bash(code:*)",
      "Bash(code --no-sandbox --user-data-dir=/root/.vscode-root --install-extension ms-python.python --force)",
      "WebFetch(domain:github.com)",
      "WebSearch",
      "Bash(claude mcp:*)",
      "Bash(sh)",
      "Bash(export PATH=\"$HOME/.local/bin:$PATH\")",
      "Bash(uvx:*)",
      "Bash(npx:*)",
      "Bash(plugin:*)",
      "Bash(WebFetch(domain:snyk.io)"
    ],
    "deny": [],
    "ask": []
  }
}
EOF

print_status "✓ Configuration files created"

################################################################################
# 6. Setup Environment Variables
################################################################################
print_section "Step 6/7: Configuring Environment Variables"

print_status "Adding environment variables to ~/.bashrc..."

# Create backup of bashrc
if [ -f ~/.bashrc ]; then
    cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
    print_status "✓ Backed up ~/.bashrc"
fi

# Add environment setup to bashrc if not already there
if ! grep -q "# Claude Code Environment Setup" ~/.bashrc; then
    cat >> ~/.bashrc <<'EOF'

# =============================================================================
# Claude Code Environment Setup
# =============================================================================

# NVM (Node Version Manager)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# UV Python package manager
export PATH="$HOME/.local/bin:$PATH"

# Claude Code environment
export CLAUDECODE=1
export CLAUDE_CODE_ENTRYPOINT=cli
EOF
    print_status "✓ Environment variables added to ~/.bashrc"
else
    print_status "✓ Environment variables already configured"
fi

# Source the updated bashrc for current session
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
export PATH="$HOME/.local/bin:$PATH"
export CLAUDECODE=1
export CLAUDE_CODE_ENTRYPOINT=cli

################################################################################
# 7. Install MCP Servers
################################################################################
print_section "Step 7/7: Installing MCP Servers"

print_status "MCP servers need to be installed from within a project directory."
echo ""
read -p "Do you want to install MCP servers now? (requires a project directory) [Y/n]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    print_status "Checking for project directory..."

    # Try to find a suitable directory
    if [ -d "$HOME/projects" ]; then
        PROJECT_DIR="$HOME/projects"
    elif [ -d "$HOME/workspace" ]; then
        PROJECT_DIR="$HOME/workspace"
    elif [ -d "$HOME/dev" ]; then
        PROJECT_DIR="$HOME/dev"
    else
        PROJECT_DIR="$HOME"
    fi

    echo ""
    read -p "Enter project directory path (default: $PROJECT_DIR): " user_project_dir
    PROJECT_DIR="${user_project_dir:-$PROJECT_DIR}"

    if [ ! -d "$PROJECT_DIR" ]; then
        print_status "Creating project directory: $PROJECT_DIR"
        mkdir -p "$PROJECT_DIR"
    fi

    cd "$PROJECT_DIR"
    print_status "Installing MCP servers in: $PROJECT_DIR"
    echo ""

    # Install MCP servers
    print_status "[1/8] Installing Filesystem MCP..."
    if claude mcp add --transport stdio filesystem -- npx -y @modelcontextprotocol/server-filesystem "$HOME" 2>/dev/null; then
        echo "  ✓ Filesystem MCP installed"
    else
        print_warning "  ⚠ Filesystem MCP already exists or failed"
    fi

    print_status "[2/8] Installing Memory MCP..."
    if claude mcp add --transport stdio memory -- npx -y @modelcontextprotocol/server-memory 2>/dev/null; then
        echo "  ✓ Memory MCP installed"
    else
        print_warning "  ⚠ Memory MCP already exists or failed"
    fi

    print_status "[3/8] Installing GitHub MCP..."
    if claude mcp add --transport stdio github -- npx -y @modelcontextprotocol/server-github 2>/dev/null; then
        echo "  ✓ GitHub MCP installed"
    else
        print_warning "  ⚠ GitHub MCP already exists or failed"
    fi

    print_status "[4/8] Installing Puppeteer MCP..."
    if claude mcp add --transport stdio puppeteer -- npx -y @modelcontextprotocol/server-puppeteer 2>/dev/null; then
        echo "  ✓ Puppeteer MCP installed (screenshot-based)"
    else
        print_warning "  ⚠ Puppeteer MCP already exists or failed"
    fi

    print_status "[5/8] Installing Playwright MCP..."
    if claude mcp add --transport stdio playwright -- npx -y @microsoft/playwright-mcp 2>/dev/null; then
        echo "  ✓ Playwright MCP installed (accessibility tree)"
    else
        print_warning "  ⚠ Playwright MCP already exists or failed"
    fi

    print_status "[6/8] Installing Git MCP..."
    if claude mcp add --transport stdio git -- uvx mcp-server-git 2>/dev/null; then
        echo "  ✓ Git MCP installed"
    else
        print_warning "  ⚠ Git MCP already exists or failed"
    fi

    print_status "[7/8] Installing SQLite MCP..."
    if claude mcp add --transport stdio sqlite -- uvx mcp-server-sqlite 2>/dev/null; then
        echo "  ✓ SQLite MCP installed"
    else
        print_warning "  ⚠ SQLite MCP already exists or failed"
    fi

    print_status "[8/8] Brave Search MCP (skipped - requires API key)"
    print_warning "  ⚠ To add Brave Search, run:"
    echo "      claude mcp add --transport stdio brave-search -- npx -y @modelcontextprotocol/server-brave-search"

    echo ""
    print_status "✓ MCP installation complete!"
    print_status "Verify with: claude mcp list"

    cd - > /dev/null 2>&1
else
    print_warning "Skipping MCP installation."
    print_status "To install MCPs later, run these commands from your project directory:"
    echo ""
    echo "  cd /your/project/directory"
    echo "  claude mcp add --transport stdio filesystem -- npx -y @modelcontextprotocol/server-filesystem \"\$HOME\""
    echo "  claude mcp add --transport stdio memory -- npx -y @modelcontextprotocol/server-memory"
    echo "  claude mcp add --transport stdio github -- npx -y @modelcontextprotocol/server-github"
    echo "  claude mcp add --transport stdio puppeteer -- npx -y @modelcontextprotocol/server-puppeteer"
    echo "  claude mcp add --transport stdio playwright -- npx -y @microsoft/playwright-mcp"
    echo "  claude mcp add --transport stdio git -- uvx mcp-server-git"
    echo "  claude mcp add --transport stdio sqlite -- uvx mcp-server-sqlite"
    echo ""
fi

################################################################################
# 8. Create Documentation
################################################################################
print_status "Creating documentation..."

cat > ~/CLAUDE_SETUP_README.md <<'EOF'
# Claude Code Complete Setup

This is a complete Claude Code installation with all components.

## What was installed:

1. **Claude Code CLI** - The main Claude Code command-line interface
2. **Plugin Marketplaces** - Multiple plugin stores with 100+ plugins and agents
   - claude-code-workflows: 64+ plugins, 87+ specialized agents
   - claude-code-marketplace: Community-curated plugins and tools
3. **MCP Servers** - Model Context Protocol servers for extended functionality (8 servers)
4. **Configuration Files** - Settings and permissions
5. **Environment Setup** - Configured in ~/.bashrc

## Directory Structure

```
~/.claude/
├── plugins/
│   └── marketplaces/
│       ├── claude-code-workflows/     # 64+ plugins, 87+ agents
│       └── claude-code-marketplace/   # Community plugins
├── settings.json                       # Plugin configuration
├── settings.local.json                 # Permissions and local settings
└── [other directories]
```

## Plugin Marketplaces

### 1. claude-code-workflows (wshobson/agents)
Production-ready workflow orchestration with 64+ focused plugins, 87+ specialized agents, and 44+ tools.

### 2. claude-code-marketplace (ananddtyagi)
Community-curated collection of high-quality, open-source Claude Code plugins.

### Managing Marketplaces

```bash
# List all marketplaces
claude plugin marketplace list

# Add a new marketplace
claude plugin marketplace add user/repo

# Update all marketplaces
claude plugin marketplace update

# Update specific marketplace
claude plugin marketplace update marketplace-name
```

## Available Plugins (claude-code-workflows)

The claude-code-workflows marketplace includes 64+ plugins across categories:

### Backend Development
- backend-development
- backend-api-security
- api-scaffolding
- api-testing-observability
- database-design
- database-migrations

### Frontend & Mobile
- frontend-mobile-development
- frontend-mobile-security
- multi-platform-apps

### DevOps & Infrastructure
- cloud-infrastructure
- kubernetes-operations
- cicd-automation
- deployment-strategies
- observability-monitoring

### Testing & Quality
- unit-testing
- tdd-workflows
- performance-testing-review
- security-scanning

### Documentation & Code Quality
- code-documentation
- documentation-generation
- code-review-ai
- code-refactoring

**And many more!** See the full list:
```bash
ls ~/.claude/plugins/marketplaces/claude-code-workflows/plugins/
ls ~/.claude/plugins/marketplaces/claude-code-marketplace/plugins/
```

## MCP Servers Configured

The following **8 MCP servers** can be installed:

1. **filesystem** - File system access and operations
2. **memory** - Persistent memory across sessions
3. **github** - GitHub integration (issues, PRs, repos)
4. **puppeteer** - Browser automation (screenshot-based)
5. **playwright** - Browser automation (accessibility tree, by Microsoft)
   - Uses structured data instead of screenshots
   - More deterministic and reliable than pixel-based automation
   - No vision models needed
6. **git** - Git operations and repository management
7. **sqlite** - SQLite database operations
8. **brave-search** - Web search capabilities (optional, requires API key)

### Playwright vs Puppeteer

Both provide browser automation but with different approaches:

- **Puppeteer**: Screenshot-based, uses visual models
- **Playwright**: Accessibility tree-based, uses structured data
  - More reliable for form filling and navigation
  - Better for automated testing
  - Developed by Microsoft

## Getting Started

1. **Restart your terminal** (or run `source ~/.bashrc`):
   ```bash
   source ~/.bashrc
   ```

2. **Authenticate with Claude:**
   ```bash
   claude auth login
   ```

3. **Navigate to a project directory:**
   ```bash
   cd /your/project
   ```

4. **Install MCPs** (if not done during setup):
   ```bash
   claude mcp add --transport stdio filesystem -- npx -y @modelcontextprotocol/server-filesystem "$HOME"
   claude mcp add --transport stdio memory -- npx -y @modelcontextprotocol/server-memory
   claude mcp add --transport stdio github -- npx -y @modelcontextprotocol/server-github
   claude mcp add --transport stdio puppeteer -- npx -y @modelcontextprotocol/server-puppeteer
   claude mcp add --transport stdio playwright -- npx -y @microsoft/playwright-mcp
   claude mcp add --transport stdio git -- uvx mcp-server-git
   claude mcp add --transport stdio sqlite -- uvx mcp-server-sqlite
   ```

5. **Start Claude:**
   ```bash
   claude
   ```

6. **Enable additional plugins:**

   Edit `~/.claude/settings.json` and add plugins:
   ```json
   {
     "enabledPlugins": {
       "backend-development@claude-code-workflows": true,
       "frontend-mobile-development@claude-code-workflows": true
     }
   }
   ```

## Useful Commands

### MCP Management
```bash
# List all MCP servers
claude mcp list

# Check MCP server status
claude mcp get <server-name>

# Remove an MCP server
claude mcp remove <server-name>
```

### Plugin Marketplace Management
```bash
# List all marketplaces
claude plugin marketplace list

# Update all marketplaces
claude plugin marketplace update

# Update specific marketplace
claude plugin marketplace update claude-code-workflows

# Add a new marketplace
claude plugin marketplace add user/repo

# Remove a marketplace
claude plugin marketplace remove marketplace-name
```

### Plugin Management
```bash
# Install a plugin
claude plugin install plugin-name

# Install from specific marketplace
claude plugin install plugin-name@marketplace-name

# List enabled plugins
cat ~/.claude/settings.json

# Browse available plugins
ls ~/.claude/plugins/marketplaces/claude-code-workflows/plugins/
ls ~/.claude/plugins/marketplaces/claude-code-marketplace/plugins/
```

### General
```bash
# Start Claude in a directory
cd /your/project && claude

# Check Claude Code version
claude --version

# Get help
claude --help
```

## Environment Variables

The following are configured in ~/.bashrc:

- `NVM_DIR` - Node Version Manager directory
- `PATH` - Includes ~/.local/bin for UV
- `CLAUDECODE=1` - Indicates Claude Code environment
- `CLAUDE_CODE_ENTRYPOINT=cli` - Sets CLI as entrypoint

## Permissions

The setup includes pre-approved permissions for common operations:
- Package management (npm, pip, apt)
- Version managers (nvm, pyenv)
- Development tools (code, git)
- Web operations (wget, curl, WebSearch, WebFetch)
- MCP operations
- Plugin operations

See `~/.claude/settings.local.json` for the full list.

## Customization

### Enable More Plugins

Browse available plugins:
```bash
ls ~/.claude/plugins/marketplaces/claude-code-workflows/plugins/
ls ~/.claude/plugins/marketplaces/claude-code-marketplace/plugins/
```

Add to `~/.claude/settings.json`:
```json
{
  "enabledPlugins": {
    "plugin-name@claude-code-workflows": true
  }
}
```

### Add Custom Permissions

Edit `~/.claude/settings.local.json` to add custom permissions to the `allow` array.

## Troubleshooting

### MCP servers not connecting

1. Check server status: `claude mcp list`
2. Verify Node.js/npm: `node --version && npm --version`
3. Verify UV installation: `uvx --version`
4. Re-install MCPs from your project directory

### Plugins not showing up

1. Verify plugin marketplaces:
   ```bash
   ls ~/.claude/plugins/marketplaces/
   ls ~/.claude/plugins/marketplaces/claude-code-workflows/plugins/
   ls ~/.claude/plugins/marketplaces/claude-code-marketplace/plugins/
   ```
2. Check settings: `cat ~/.claude/settings.json`
3. Update all marketplaces: `claude plugin marketplace update`

### Authentication issues

```bash
claude auth login
claude auth status
```

### Environment not loaded

```bash
source ~/.bashrc
```

## Backup Your Configuration

To backup your Claude configuration:
```bash
tar -czf claude-backup-$(date +%Y%m%d).tar.gz ~/.claude/
```

## Migration to Another System

1. Copy this setup script to the new system
2. Run: `./claude-setup-complete.sh`
3. Copy your credentials: `~/.claude/.credentials.json` (if needed)
4. Copy custom settings if you've modified them

## Resources

- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [Plugin Marketplaces Documentation](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
- [MCP Documentation](https://modelcontextprotocol.io/)

### Plugin Marketplace Repositories
- [claude-code-workflows](https://github.com/wshobson/agents) - 64+ plugins, 87+ agents
- [claude-code-marketplace](https://github.com/ananddtyagi/claude-code-marketplace) - Community plugins
- [Community Marketplace Directory](https://claudecodemarketplace.com/)

### MCP Server Resources
- [MCP Servers Documentation](https://modelcontextprotocol.io/docs)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp) - Microsoft's browser automation
- [Official MCP Servers](https://github.com/modelcontextprotocol)

## Support

For issues or questions:
- Claude Code: https://github.com/anthropics/claude-code/issues
- claude-code-workflows: https://github.com/wshobson/agents/issues
- claude-code-marketplace: https://github.com/ananddtyagi/claude-code-marketplace/issues
EOF

print_status "✓ Documentation created at ~/CLAUDE_SETUP_README.md"

################################################################################
# Summary
################################################################################

print_section "Installation Complete!"

echo -e "${GREEN}✅ Installed Components:${NC}"
echo "  ✓ Claude Code CLI"
echo "  ✓ Node.js & npm (via nvm)"
echo "  ✓ UV (Python package manager for Python MCPs)"
echo "  ✓ 2 Plugin Marketplaces:"
echo "    • claude-code-workflows (64+ plugins, 87+ agents)"
echo "    • claude-code-marketplace (community plugins)"
echo "  ✓ Configuration files with permissions"
echo "  ✓ Environment variables (in ~/.bashrc)"
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    echo "  ✓ 8 MCP Servers (filesystem, memory, github, puppeteer, playwright, git, sqlite)"
else
    echo "  ⚠ MCP Servers (installation skipped)"
fi
echo ""

echo -e "${CYAN}📚 Documentation:${NC}"
echo "  ~/CLAUDE_SETUP_README.md"
echo ""

echo -e "${CYAN}🔌 Plugin Marketplaces:${NC}"
echo "  • claude-code-workflows: ~/.claude/plugins/marketplaces/claude-code-workflows/"
echo "  • claude-code-marketplace: ~/.claude/plugins/marketplaces/claude-code-marketplace/"
echo "  • Commands: claude plugin marketplace list | update"
echo ""

echo -e "${CYAN}🚀 Next Steps:${NC}"
echo "  1. Restart your terminal or run: ${YELLOW}source ~/.bashrc${NC}"
echo "  2. Authenticate: ${YELLOW}claude auth login${NC}"
echo "  3. Navigate to a project: ${YELLOW}cd /your/project${NC}"
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "  4. Install MCPs (see README for commands)"
    echo "  5. Start Claude: ${YELLOW}claude${NC}"
else
    echo "  4. Start Claude: ${YELLOW}claude${NC}"
fi
echo ""

echo -e "${CYAN}📦 Browse Available Plugins:${NC}"
echo "  ls ~/.claude/plugins/marketplaces/claude-code-workflows/plugins/"
echo "  ls ~/.claude/plugins/marketplaces/claude-code-marketplace/plugins/"
echo ""

echo -e "${CYAN}⚙️  Enable Plugins:${NC}"
echo "  Edit: ~/.claude/settings.json"
echo ""

echo -e "${GREEN}========================================================================${NC}"
echo -e "${GREEN}Setup complete! Read ~/CLAUDE_SETUP_README.md for detailed information.${NC}"
echo -e "${GREEN}========================================================================${NC}"
echo ""

exit 0
