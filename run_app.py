# run_app.py
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the app
from name_address_validator.app import main

if __name__ == "__main__":
    main()