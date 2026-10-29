"""PyInstaller runtime hook for the frozen-build tweaks.

The patching itself lives in ``kadishutu._frozen`` so it can be exercised by
tests without PyInstaller.
"""
from kadishutu._frozen import apply

apply()
