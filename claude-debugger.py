#!/usr/bin/env python3
"""
Claude Code Setup Debugger
This script helps identify whether Claude Code SDK or CLI is being used in the environment.
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
import importlib.util

def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def check_claude_cli():
    """Check for Claude Code CLI installation and configuration."""
    print_section("Claude Code CLI Check")
    
    # Check if claude command exists
    claude_path = shutil.which("claude")
    if claude_path:
        print(f"✓ Claude CLI found at: {claude_path}")
        
        # Get version
        stdout, stderr, code = run_command("claude --version")
        if code == 0:
            print(f"  Version: {stdout}")
        
        # Check for config files
        config_paths = [
            Path.home() / ".claude" / "config.json",
            Path.home() / ".config" / "claude" / "config.json",
            Path("/etc/claude/config.json"),
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                print(f"  Config found: {config_path}")
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        # Don't print sensitive info, just structure
                        print(f"    Config keys: {list(config.keys())}")
                except Exception as e:
                    print(f"    Could not read config: {e}")
    else:
        print("✗ Claude CLI not found in PATH")
    
    # Check for common CLI installation directories
    cli_dirs = [
        "/usr/local/bin/claude",
        "/usr/bin/claude",
        "/opt/claude/bin/claude",
        Path.home() / ".local" / "bin" / "claude",
    ]
    
    for cli_dir in cli_dirs:
        if Path(cli_dir).exists():
            print(f"  Found CLI binary at: {cli_dir}")

def check_claude_sdk():
    """Check for Claude Code SDK installation."""
    print_section("Claude Code SDK Check")
    
    # Check for Python SDK
    try:
        # Try to import claude_code or similar packages
        sdk_packages = [
            "claude_code",
            "claude_sdk",
            "anthropic_claude",
            "anthropic",
            "claudecode",
        ]
        
        found_sdks = []
        for package in sdk_packages:
            spec = importlib.util.find_spec(package)
            if spec:
                found_sdks.append(package)
                print(f"✓ Python package '{package}' found")
                
                # Try to get version
                try:
                    module = __import__(package)
                    if hasattr(module, '__version__'):
                        print(f"  Version: {module.__version__}")
                    print(f"  Location: {spec.origin}")
                except Exception as e:
                    print(f"  Could not load module: {e}")
        
        if not found_sdks:
            print("✗ No Claude SDK Python packages found")
    except Exception as e:
        print(f"Error checking Python packages: {e}")
    
    # Check pip list for claude-related packages
    stdout, stderr, code = run_command("pip list | grep -i claude")
    if stdout:
        print("\nInstalled pip packages with 'claude':")
        print(stdout)
    
    # Check npm for Node.js SDK
    stdout, stderr, code = run_command("npm list -g --depth=0 | grep -i claude")
    if stdout:
        print("\nGlobal npm packages with 'claude':")
        print(stdout)

def check_environment():
    """Check environment variables related to Claude."""
    print_section("Environment Variables")
    
    claude_env_vars = []
    for key, value in os.environ.items():
        if 'CLAUDE' in key.upper() or 'ANTHROPIC' in key.upper():
            # Mask potential API keys
            if 'KEY' in key.upper() or 'TOKEN' in key.upper() or 'SECRET' in key.upper():
                masked_value = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
                claude_env_vars.append(f"{key}={masked_value}")
            else:
                claude_env_vars.append(f"{key}={value}")
    
    if claude_env_vars:
        print("Claude/Anthropic related environment variables:")
        for var in claude_env_vars:
            print(f"  {var}")
    else:
        print("No Claude/Anthropic environment variables found")

def check_processes():
    """Check for running Claude-related processes."""
    print_section("Running Processes")
    
    # Check for claude processes
    stdout, stderr, code = run_command("ps aux | grep -i claude | grep -v grep")
    if stdout:
        print("Claude-related processes:")
        for line in stdout.split('\n'):
            if line.strip():
                print(f"  {line[:150]}...")  # Truncate long lines
    else:
        print("No Claude-related processes found")
    
def check_claude_launch_commands():
    """Check how Claude CLI sessions were launched."""
    print_section("Claude CLI Launch Commands")
    
    # Get detailed process info for claude commands with full command line
    stdout, stderr, code = run_command("ps auxww | grep -E 'claude' | grep -v grep | grep -v 'Claude.app'")
    
    if stdout:
        print("Active Claude CLI sessions and their launch commands:")
        print()
        
        sessions = []
        for line in stdout.split('\n'):
            if line.strip() and 'claude' in line:
                # Parse the ps output
                parts = line.split(None, 10)  # Split into max 11 parts
                if len(parts) >= 11:
                    pid = parts[1]
                    start_time = parts[8]
                    cpu_time = parts[9]
                    cmd = parts[10]
                    
                    # Filter for actual claude commands (not helpers/etc)
                    if 'claude' in cmd and not 'VibeTunnel' in cmd and not 'claude-monitor' in cmd and not 'claude-debugger' in cmd:
                        sessions.append({
                            'pid': pid,
                            'start_time': start_time,
                            'cpu_time': cpu_time,
                            'command': cmd.strip()
                        })
        
        if sessions:
            for i, session in enumerate(sessions, 1):
                print(f"Session {i}:")
                print(f"  PID: {session['pid']}")
                print(f"  Started: {session['start_time']}")
                print(f"  CPU Time: {session['cpu_time']}")
                print(f"  Command: {session['command']}")
                
                # Parse command line arguments
                if ' -' in session['command']:
                    print("  Detected arguments:")
                    cmd_parts = session['command'].split()
                    j = 0
                    while j < len(cmd_parts):
                        part = cmd_parts[j]
                        if part.startswith('-'):
                            # Get the flag and its value if present
                            flag = part
                            value = ""
                            if j + 1 < len(cmd_parts) and not cmd_parts[j + 1].startswith('-'):
                                value = cmd_parts[j + 1]
                                j += 1  # Skip the value in next iteration
                            
                            if flag == '-p' or flag == '--project':
                                print(f"    Project mode: {value if value else 'Yes'}")
                            elif flag == '-c' or flag == '--config':
                                print(f"    Config file: {value}")
                            elif flag == '-m' or flag == '--model':
                                print(f"    Model override: {value}")
                            elif flag == '--debug':
                                print("    Debug mode: Enabled")
                            elif flag == '--no-telemetry':
                                print("    Telemetry: Disabled")
                            elif flag == '--no-color':
                                print("    Color output: Disabled")
                            elif flag == '--json':
                                print("    JSON output: Enabled")
                            elif flag == '-h' or flag == '--help':
                                print("    Help mode")
                            elif flag == '-v' or flag == '--version':
                                print("    Version check")
                        j += 1
                else:
                    print("  Mode: Interactive (no arguments)")
                
                # Check working directory for this PID
                stdout2, stderr2, code2 = run_command(f"lsof -p {session['pid']} 2>/dev/null | grep 'cwd' | awk '{{print $NF}}' | head -1")
                if stdout2:
                    print(f"  Working Directory: {stdout2}")
                
                print()
        else:
            print("No active Claude CLI command sessions found")
    else:
        print("No Claude CLI processes detected")
    
    # Check for parent shell sessions that might have launched Claude
    print("\nChecking for parent shell sessions:")
    stdout, stderr, code = run_command("ps aux | grep -E '(zsh|bash).*claude' | grep -v grep")
    if stdout:
        print("Shell sessions that may have launched Claude:")
        for line in stdout.split('\n')[:5]:  # Limit to 5 lines
            if line.strip():
                print(f"  {line[:120]}...")
    
    # Check command history for recent Claude commands
    print("\nRecent Claude commands from shell history:")
    
    # Try different shell history files
    history_files = [
        Path.home() / ".zsh_history",
        Path.home() / ".bash_history",
        Path.home() / ".history",
    ]
    
    found_history = False
    for history_file in history_files:
        if history_file.exists():
            try:
                stdout, stderr, code = run_command(f"tail -1000 {history_file} 2>/dev/null | grep '^claude' | tail -5")
                if stdout:
                    found_history = True
                    print(f"  From {history_file.name}:")
                    for line in stdout.split('\n'):
                        if line.strip():
                            # Clean up zsh history format if present
                            if ': ' in line and ';' in line:
                                # zsh format: : timestamp:0;command
                                line = line.split(';', 1)[1] if ';' in line else line
                            print(f"    {line.strip()}")
            except:
                pass
    
    if not found_history:
        print("  No recent Claude commands found in shell history")

def check_docker():
    """Check if running in Docker and for Claude-related containers."""
    print_section("Docker/Container Check")
    
    # Check if we're in a container
    if Path("/.dockerenv").exists():
        print("✓ Running inside a Docker container")
    elif Path("/run/.containerenv").exists():
        print("✓ Running inside a container (Podman/other)")
    else:
        print("✗ Not running in a container (or container type not detected)")
    
    # Check for Claude-related Docker images/containers
    stdout, stderr, code = run_command("docker ps 2>/dev/null | grep -i claude")
    if code == 0 and stdout:
        print("Claude-related Docker containers:")
        print(stdout)

def check_python_runtime():
    """Check Python runtime for Claude SDK usage."""
    print_section("Python Runtime Analysis")
    
    # Check imported modules
    imported_modules = [name for name in sys.modules.keys() if 'claude' in name.lower() or 'anthropic' in name.lower()]
    if imported_modules:
        print("Currently imported Claude/Anthropic modules:")
        for mod in imported_modules:
            print(f"  {mod}")
    else:
        print("No Claude/Anthropic modules currently imported")
    
    # Check sys.path for Claude-related directories
    claude_paths = [p for p in sys.path if 'claude' in p.lower() or 'anthropic' in p.lower()]
    if claude_paths:
        print("\nClaude-related paths in sys.path:")
        for path in claude_paths:
            print(f"  {path}")

def check_network_connections():
    """Check for network connections to Anthropic endpoints."""
    print_section("Network Connections")
    
    # Check for connections to Anthropic API
    stdout, stderr, code = run_command("netstat -an 2>/dev/null | grep -E '(api.anthropic|claude.ai)' || ss -an 2>/dev/null | grep -E '(api.anthropic|claude.ai)'")
    if stdout:
        print("Connections to Anthropic endpoints:")
        print(stdout)
    else:
        print("No active connections to Anthropic endpoints detected")
    
    # Check DNS cache for Anthropic domains
    stdout, stderr, code = run_command("getent hosts api.anthropic.com claude.ai 2>/dev/null")
    if stdout:
        print("\nDNS lookups for Anthropic domains:")
        print(stdout)

def check_file_system():
    """Check file system for Claude-related files."""
    print_section("File System Analysis")
    
    # Common directories to check
    dirs_to_check = [
        Path.home() / ".claude",
        Path.home() / ".config" / "claude",
        Path("/opt/claude"),
        Path("/usr/local/claude"),
        Path("/tmp"),
    ]
    
    for dir_path in dirs_to_check:
        if dir_path.exists():
            try:
                claude_files = list(dir_path.glob("*claude*"))
                if claude_files:
                    print(f"\nClaude-related files in {dir_path}:")
                    for file in claude_files[:10]:  # Limit to 10 files
                        print(f"  {file}")
            except PermissionError:
                print(f"Permission denied accessing {dir_path}")

def main():
    """Main execution function."""
    print("="*60)
    print(" Claude Code Setup Debugger")
    print(" Detecting whether SDK or CLI is being used")
    print("="*60)
    
    # System info
    print_section("System Information")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    stdout, _, _ = run_command("uname -a")
    if stdout:
        print(f"System: {stdout}")
    
    # Run all checks
    check_claude_cli()
    check_claude_sdk()
    check_environment()
    check_processes()
    check_claude_launch_commands()
    check_docker()
    check_python_runtime()
    check_network_connections()
    check_file_system()
    
    # Summary
    print_section("Summary")
    print("Review the above information to determine your Claude Code setup.")
    print("Key indicators:")
    print("- CLI: Look for 'claude' binary in PATH, config files in ~/.claude")
    print("- SDK: Look for Python/Node packages, imported modules")
    print("- Both setups may use ANTHROPIC_API_KEY environment variable")
    print("\nFor e2b sandboxes specifically:")
    print("- Check if code is being executed via subprocess calls to 'claude' command")
    print("- Or if Python/Node SDK is being imported and used directly")

if __name__ == "__main__":
    main()