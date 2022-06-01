import subprocess
from pathlib import Path
from yukkuri_utility.core import (
    config,
)


def conv(src: Path, dst: Path):
    command: list[str] = [
        str(config.ROOT_PATH.joinpath('bin', 'realesrgan-ncnn-vulkan-20220424-windows', 'realesrgan-ncnn-vulkan.exe')),
        '-i',
        str(src),
        '-o',
        str(dst),
    ]
    subprocess.run(command, shell=True)


if __name__ == '__main__':
    pass
