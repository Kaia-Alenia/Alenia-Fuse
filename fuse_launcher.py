import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath("src"))
    from fuse.cli.main import main
    main()
