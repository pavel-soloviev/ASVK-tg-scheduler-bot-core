from pathlib import Path
import sys


# все тесты будут видеть модули бота независимо от места запуска
sys.path.append(str(Path(__file__).parent.parent))