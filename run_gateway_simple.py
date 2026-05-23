#!/usr/bin/env python3
import os
import sys

# Set encoding to UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import and run gateway
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gateway.run import start_gateway
    import asyncio
    
    print("Starting Hermes Gateway...")
    print("Press Ctrl+C to stop.")
    print()
    
    # Run the gateway
    asyncio.run(start_gateway())
except KeyboardInterrupt:
    print("\nGateway stopped by user")
except Exception as e:
    print(f"Error starting gateway: {e}")
    sys.exit(1)