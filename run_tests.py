import unittest
from pathlib import Path

def main():
    loader = unittest.TestLoader()
    tests_path = Path(__file__).parent / "tests"
    suite = loader.discover(str(tests_path))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    main()