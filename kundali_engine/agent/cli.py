"""
CLI transport for the AstroLogic agent.

Run:  python -m kundali_engine.agent.cli

This is one transport layer. The same AstroAgent core can be wired to
Flask/FastAPI (web) or Twilio (WhatsApp) with identical behaviour.
"""

from kundali_engine.agent.agent import AstroAgent


def main():
    agent = AstroAgent()

    print("AstroLogic Agent")
    print("Type 'help' for commands, 'quit' to exit.\n")

    # Opening greeting
    print(agent.handle("hello", "cli"))
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nNamaste! See you next time.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye", "goodbye"):
            print("Namaste! See you next time.")
            break

        response = agent.handle(user_input, "cli")
        print(f"\n{response}\n")


if __name__ == "__main__":
    main()
