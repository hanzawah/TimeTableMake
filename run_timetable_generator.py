import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python_scripts"))

from python_scripts import main

if __name__ == "__main__":
    main.main()