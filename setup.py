from setuptools import setup, find_packages

setup(
    name="unattend_my_iso",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "unattend_my_iso=unattend_my_iso.main:main",
        ],
    },
)
