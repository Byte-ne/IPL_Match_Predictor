from .runtime import require_supported_python
from .cli import main

if __name__ == "__main__":
    require_supported_python()
    main()
