"""
Termux Environment Adapter
Automatically detects Termux/Android and adapts commands, paths, and tool suggestions
"""
import os
import subprocess
import sys
from typing import Optional, Tuple, Dict, List


class TermuxAdapter:
    """Detect and adapt Open Vulnera for Termux environment"""
    
    @staticmethod
    def is_termux() -> bool:
        """Check if running in Termux"""
        return (
            os.environ.get('TERMUX_VERSION') is not None
            or os.path.exists('/data/data/com.termux')
            or os.environ.get('PREFIX', '').startswith('/data/data/com.termux')
        )
    
    @staticmethod
    def is_android() -> bool:
        """Check if running on Android"""
        return (
            os.path.exists('/system/build.prop')
            or os.environ.get('ANDROID_ROOT') is not None
        )
    
    @staticmethod
    def adapt_install_command(tool: str) -> str:
        """Convert install commands to Termux format"""
        if TermuxAdapter.is_termux():
            # Termux uses pkg, not apt
            return f"pkg install -y {tool}"
        return f"apt-get install -y {tool}"
    
    @staticmethod
    def adapt_path(path: str) -> str:
        """Adapt file paths for Termux"""
        if not TermuxAdapter.is_termux():
            return path
        
        # Replace common Unix paths with Termux equivalents
        replacements = {
            '/home/user': os.path.expanduser('~'),
            '/home/$USER': os.path.expanduser('~'),
            '/root': os.path.expanduser('~'),
            '/opt': os.environ.get('PREFIX', '/data/data/com.termux/files/usr'),
            '/usr/local': os.environ.get('PREFIX', '/data/data/com.termux/files/usr'),
            '/usr/share': os.environ.get('PREFIX', '/data/data/com.termux/files/usr/share'),
        }
        
        adapted = path
        for old, new in replacements.items():
            if adapted.startswith(old):
                adapted = adapted.replace(old, new, 1)
                break
        
        return adapted
    
    @staticmethod
    def adapt_command_for_environment(cmd: str) -> str:
        """
        Adapt shell commands to work in current environment
        - Remove sudo from commands if on Termux
        - Replace apt-get with pkg on Termux
        - Adapt paths appropriately
        """
        if not TermuxAdapter.is_termux():
            return cmd
        
        adapted = cmd
        
        # Remove sudo - Termux doesn't need it
        adapted = adapted.replace('sudo ', '').replace('sudo', '')
        
        # Replace apt-get with pkg (Termux package manager)
        adapted = adapted.replace('apt-get', 'pkg')
        adapted = adapted.replace('apt-get install', 'pkg install -y')
        adapted = adapted.replace('apt install', 'pkg install -y')
        
        # Replace apt with pkg
        if adapted.startswith('apt '):
            adapted = adapted.replace('apt ', 'pkg ', 1)
        
        # Adapt common paths
        adapted = TermuxAdapter.adapt_path(adapted)
        
        return adapted
    
    @staticmethod
    def validate_command(cmd: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if command can run in current environment
        Returns: (is_valid, error_message_if_invalid)
        """
        if not TermuxAdapter.is_termux():
            return (True, None)
        
        # Check for incompatible commands
        incompatible_patterns = [
            ('apt-get', 'Use "pkg" instead of "apt-get" on Termux'),
            ('apt install', 'Use "pkg install" instead of "apt install" on Termux'),
            ('sudo ', 'Termux does not support sudo. Remove "sudo" from command.'),
            ('aircrack', 'aircrack-ng not available on Termux (no monitor mode)'),
            ('metasploit', 'Metasploit unstable on Termux. Use custom Python scripts or sqlmap instead.'),
        ]
        
        cmd_lower = cmd.lower()
        for pattern, error_msg in incompatible_patterns:
            if pattern in cmd_lower:
                return (False, error_msg)
        
        return (True, None)
        """Check if a tool is available (cross-platform aware)"""
        try:
            result = subprocess.run(
                f"which {tool}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def get_tool_alternatives(tool: str) -> List[str]:
        """Get Termux-compatible alternatives when tool unavailable"""
        alternatives = {
            'aircrack-ng': ['hashcat'],  # No aircrack on Termux
            'metasploit': ['custom_python_scripts', 'sqlmap'],  # Avoid Metasploit on Termux
            'burp': ['mitmproxy', 'curl', 'python_requests'],  # Use terminal tools
            'wireshark': ['tcpdump', 'python_scapy'],  # Use CLI tools
            'nessus': ['openvas', 'nmap'],  # Use available scanners
        }
        return alternatives.get(tool.lower(), [])
    
    @staticmethod
    def check_tool_compatibility(tool: str) -> Tuple[bool, Optional[str]]:
        """
        Check if tool is compatible with current environment
        Returns: (is_compatible, reason_if_not)
        """
        if not TermuxAdapter.is_termux():
            return (True, None)
        
        incompatible_tools = {
            'aircrack-ng': 'Requires monitor mode (not available on Android)',
            'metasploit': 'Unstable on Termux, many modules broken',
            'burp': 'GUI tool, not available on Termux',
            'wireshark': 'GUI tool, requires libpcap',
            'impacket_smbclient': 'Requires Windows file sharing access',
            'evil-winrm': 'Windows-only tool',
        }
        
        tool_lower = tool.lower()
        for incomp_tool, reason in incompatible_tools.items():
            if incomp_tool in tool_lower:
                return (False, reason)
        
        return (True, None)
    
    @staticmethod
    def suggest_termux_alternatives(task: str) -> Optional[str]:
        """Suggest Termux-friendly alternatives for tasks"""
        suggestions = {
            'wireless_cracking': 'WPA2 cracking not possible on Termux (no monitor mode). Focus on: web attacks, OSINT, network scanning',
            'packet_capture': 'Live packet capture requires root. Use: tcpdump, scapy',
            'gui_tools': 'GUI tools unavailable on Termux. Use: terminal-based alternatives (mitmproxy, curl, python)',
            'metasploit': 'Metasploit unstable on Termux. Use: custom Python exploits, sqlmap, manual exploitation',
            'windows_tools': 'Windows tools not available on Android. Focus on: web exploitation, OSINT, protocol analysis',
        }
        
        for key, suggestion in suggestions.items():
            if key in task.lower():
                return suggestion
        
        return None
    
    @staticmethod
    def get_environment_context() -> Dict[str, str]:
        """Get environment context for system prompts"""
        context = {
            'is_termux': 'Yes' if TermuxAdapter.is_termux() else 'No',
            'is_android': 'Yes' if TermuxAdapter.is_android() else 'No',
            'prefix': os.environ.get('PREFIX', '/usr'),
            'home': os.path.expanduser('~'),
            'shell': os.environ.get('SHELL', '/bin/sh'),
        }
        
        if TermuxAdapter.is_termux():
            context['package_manager'] = 'pkg (not apt-get)'
            context['note'] = 'Use "pkg install" not "apt-get install". No sudo. Use $PREFIX and $HOME paths.'
        
        return context


def get_system_prompt_supplement() -> str:
    """Get environment-aware supplement for system prompt"""
    if not TermuxAdapter.is_termux():
        return ""
    
    return """
**CRITICAL ENVIRONMENT: Running on Termux/Android**

Package Management:
- Use: `pkg install -y TOOL_NAME` 
- NOT: `apt-get`, `apt`, or `yum`
- For tools not in pkg repos: install from source or via language-specific managers (pip, go, etc)

No Sudo:
- Termux has no sudo - you already have elevated access in your home directory
- Don't use `sudo` in any commands
- For system-wide changes, use `pkg` package manager

Paths:
- Use $HOME, $PREFIX, relative paths only
- NOT /home/user (that's Linux)
- NOT /usr/local (use $PREFIX instead)
- NOT /root (use $HOME instead)

Tools That Work Great on Termux:
✓ Port scanning: nmap, masscan, rustscan
✓ Web exploitation: sqlmap, custom Python scripts
✓ OSINT: subfinder, amass, theHarvester
✓ Password attacks: john, hashcat
✓ File analysis: strings, hexdump, file

Tools That DON'T Work:
✗ Wireless attacks (aircrack-ng) - No monitor mode
✗ GUI tools (Burp Suite, Wireshark) 
✗ Metasploit - Unstable on Termux
✗ Kernel exploits - Different OS
✗ Windows-specific tools

Always check tool availability before suggesting:
Instead of: "run nmap"
Do this: "check with 'which nmap', if missing run 'pkg install -y nmap'"

When tool unavailable, suggest Termux-compatible alternative.
"""
