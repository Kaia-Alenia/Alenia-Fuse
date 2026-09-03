import sys
import os
import unicodedata
import encodings.idna

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath("src"))
    if "--cli-engine" in sys.argv:
        sys.argv.remove("--cli-engine")
        from alenia_porter.headless import main
        main()
    else:
        from alenia_porter.cli.main import main
        main()
