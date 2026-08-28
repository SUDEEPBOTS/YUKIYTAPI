import os
from setuptools import setup, find_packages

long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="yukiytapi",
    version="1.0.0",
    description="Official High-Speed Python SDK & API Wrapper for Yuki YouTube Music Streaming Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SUDEEPBOTS",
    author_email="sudeepbots@gmail.com",
    url="https://github.com/SUDEEPBOTS/YUKIYTAPI",
    project_urls={
        "Documentation": "https://yukiapi.site/docs",
        "Source": "https://github.com/SUDEEPBOTS/YUKIYTAPI",
        "Tracker": "https://github.com/SUDEEPBOTS/YUKIYTAPI/issues",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
    ],
    keywords="yukiytapi yukimusic telegram-music-bot youtube-stream pytgcalls audio downloader",
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
    ],
    entry_points={
        "console_scripts": [
            "yuki-dl=yukiytapi.cli:main",
            "yukiytapi=yukiytapi.cli:main",
        ],
    },
)
