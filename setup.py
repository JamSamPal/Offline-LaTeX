from setuptools import setup, find_packages

setup(
    name="autorun",
    version="0.1",
    py_modules=["autorun"],
    entry_points={
        "console_scripts": [
            "autorun = autorun:main",
        ],
    },
)
