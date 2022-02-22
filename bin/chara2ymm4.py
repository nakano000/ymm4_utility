import sys
import os

lib_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../library/python')
)
sys.path.append(lib_path)

if __name__ == "__main__":
    from yukkuri_utility.tool.chara2ymm4 import run
    run()