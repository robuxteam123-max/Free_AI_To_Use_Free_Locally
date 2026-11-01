"""Your AI's launch file. The improvement agent may update this file.

This file starts the local browser AI. The more complex implementation lives in
smart_ai.py. Automatic upgrades only write to main.py; core suggestions are
saved as reviewable proposals.
"""
from smart_ai import main as start_browser


def main():
    print("Starting MyFirstAI Smart: local, no paid API keys.")
    start_browser()


if __name__ == "__main__":
    main()
