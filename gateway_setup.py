#!/usr/bin/env python3
"""
Simple gateway runner that bypasses Unicode issues on Windows.
"""
import os
import sys
import asyncio

# Set encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['HERMES_QUIET'] = '1'
os.environ['HERMES_EXEC_ASK'] = '1'

# Add project to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

def main():
    print("=" * 60)
    print("Hermes Gateway Setup")
    print("=" * 60)
    print()
    print("Available platforms:")
    print("1. Telegram (recommended)")
    print("2. Discord")
    print("3. Slack")
    print("4. Run gateway with current configuration")
    print("5. Exit")
    print()
    
    choice = input("Select option [1-5]: ").strip()
    
    if choice == "1":
        setup_telegram()
    elif choice == "2":
        setup_discord()
    elif choice == "3":
        setup_slack()
    elif choice == "4":
        run_gateway()
    elif choice == "5":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice")
        sys.exit(1)

def setup_telegram():
    print("\n" + "=" * 60)
    print("Telegram Bot Setup")
    print("=" * 60)
    print()
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot to create a new bot")
    print("3. Follow the instructions to get your bot token")
    print("4. Enter your bot token below (format: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)")
    print()
    
    token = input("Bot token: ").strip()
    
    if not token:
        print("No token provided. Skipping Telegram setup.")
        return
    
    # Add to .env file
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path, 'a') as f:
        f.write(f"\nTELEGRAM_BOT_TOKEN={token}\n")
    
    print(f"\n✓ Telegram bot token added to {env_path}")
    print("\nNext steps:")
    print("1. Start your bot in Telegram by sending /start")
    print("2. Run the gateway with option 4")
    print()

def setup_discord():
    print("\n" + "=" * 60)
    print("Discord Bot Setup")
    print("=" * 60)
    print()
    print("1. Go to https://discord.com/developers/applications")
    print("2. Create New Application → Bot → Copy Token")
    print("3. Enter your bot token below")
    print()
    
    token = input("Bot token: ").strip()
    
    if not token:
        print("No token provided. Skipping Discord setup.")
        return
    
    # Add to .env file
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path, 'a') as f:
        f.write(f"\nDISCORD_BOT_TOKEN={token}\n")
    
    print(f"\n✓ Discord bot token added to {env_path}")
    print()

def setup_slack():
    print("\n" + "=" * 60)
    print("Slack Bot Setup")
    print("=" * 60)
    print()
    print("1. Go to https://api.slack.com/apps")
    print("2. Create New App → From scratch")
    print("3. Go to OAuth & Permissions → Bot Token Scopes")
    print("4. Add these scopes: chat:write, im:write, mpim:write")
    print("5. Install to workspace and copy Bot User OAuth Token")
    print("6. Enter your bot token below (starts with xoxb-)")
    print()
    
    token = input("Bot token: ").strip()
    
    if not token:
        print("No token provided. Skipping Slack setup.")
        return
    
    # Add to .env file
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path, 'a') as f:
        f.write(f"\nSLACK_BOT_TOKEN={token}\n")
    
    print(f"\n✓ Slack bot token added to {env_path}")
    print()

def run_gateway():
    print("\n" + "=" * 60)
    print("Starting Hermes Gateway")
    print("=" * 60)
    print()
    
    try:
        # Import here to avoid loading if not needed
        from gateway.run import start_gateway
        
        print("Gateway starting...")
        print("Press Ctrl+C to stop.")
        print()
        
        # Run the gateway
        asyncio.run(start_gateway())
    except KeyboardInterrupt:
        print("\nGateway stopped by user")
    except Exception as e:
        print(f"\nError starting gateway: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have API keys in ~/.hermes/.env")
        print("2. Check that the platform is properly configured")
        print("3. Try running with HERMES_QUIET=1 hermes gateway run")
        sys.exit(1)

if __name__ == "__main__":
    main()