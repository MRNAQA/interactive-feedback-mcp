# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
import os
import sys
import json
import tempfile
import subprocess

from typing import Annotated, Dict

from fastmcp import FastMCP
from pydantic import Field

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")

def launch_feedback_ui(project_directory: str, summary: str) -> dict[str, str]:
    # Create a temporary file for the feedback result
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        # Get the path to feedback_ui.py relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")

        # Run feedback_ui.py as a separate process
        # NOTE: There appears to be a bug in uv, so we need
        # to pass a bunch of special flags to make this work
        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--project-directory", project_directory,
            "--prompt", summary,
            "--output-file", output_file
        ]
        result = subprocess.run(
            args,
            check=False,
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )
        if result.returncode != 0:
            raise Exception(f"Failed to launch feedback UI: {result.returncode}")

        # Read the result from the temporary file
        with open(output_file, 'r') as f:
            result_data = json.load(f) # Renamed to avoid conflict
        os.unlink(output_file)
        return result_data # Use renamed variable
    except Exception as e:
        if 'output_file' in locals() and os.path.exists(output_file): # Check if output_file was defined
            os.unlink(output_file)
        raise e

def first_line(text: str) -> str:
    return text.split("\n")[0].strip()

@mcp.tool()
def interactive_feedback(
    project_directory: Annotated[str, Field(description="Full path to the project directory")],
    summary: Annotated[str, Field(description="Short, one-line summary of the changes")],
) -> Dict[str, str]:
    """Request interactive feedback for a given project directory and summary"""
    return launch_feedback_ui(first_line(project_directory), first_line(summary))

# New function for the entry point
def main_stdio_server():
    """Runs the MCP server in stdio mode."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main_stdio_server() 
