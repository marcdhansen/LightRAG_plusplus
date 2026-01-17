append to pyproject.toml:

[tool.uv]
required-environments = [
    "sys_platform == 'darwin' and platform_machine == 'x86_64'",
]

from: https://docling-project.github.io/docling/getting_started/installation/

Installation on macOS Intel (x86_64)
When installing Docling on macOS with Intel processors, you might encounter errors with PyTorch compatibility. This happens because newer PyTorch versions (2.6.0+) no longer provide wheels for Intel-based Macs.

If you're using an Intel Mac, install Docling with compatible PyTorch Note: PyTorch 2.2.2 requires Python 3.12 or lower. Make sure you're not using Python 3.13+.


# For uv users
uv add torch==2.2.2 torchvision==0.17.2 docling

# For pip users
pip install "docling[mac_intel]"
