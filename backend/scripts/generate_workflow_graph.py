#!/usr/bin/env python3
"""
Script to generate LangGraph workflow visualization.

This script initializes the LangGraph agent and exports the workflow graph as PNG and ASCII.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Set required environment variables with defaults
os.environ.setdefault('ANTHROPIC_API_KEY', 'sk-test-key')
os.environ.setdefault('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')
os.environ.setdefault('DATABASE_URL', 'postgresql://user:pass@localhost/db')

from app.services.langgraph_agent_service import get_langgraph_agent


def main():
    """Generate workflow graph visualizations."""
    print("Initializing LangGraph Document Agent...")

    try:
        agent = get_langgraph_agent()
        print("✓ Agent initialized successfully")

        # Generate PNG
        print("\nGenerating PNG graph...")
        try:
            png_path = agent.export_graph_as_png("docs/langgraph_workflow.png")
            print(f"✓ PNG graph saved to: {png_path}")
        except Exception as e:
            print(f"✗ Failed to generate PNG: {e}")

        # Generate ASCII
        print("\nGenerating ASCII graph...")
        try:
            ascii_graph = agent.get_graph_ascii()
            ascii_path = "docs/langgraph_workflow_ascii.txt"
            Path(ascii_path).parent.mkdir(parents=True, exist_ok=True)
            with open(ascii_path, 'w') as f:
                f.write(ascii_graph)
            print(f"✓ ASCII graph saved to: {ascii_path}")
            print("\nASCII Preview:")
            print("=" * 80)
            print(ascii_graph)
            print("=" * 80)
        except Exception as e:
            print(f"✗ Failed to generate ASCII: {e}")

        print("\n✓ Workflow graph generation complete!")

    except Exception as e:
        print(f"✗ Error initializing agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
