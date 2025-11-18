from setuptools import setup, find_packages

setup(
    name="nexuscore",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core
        "fastapi>=0.95.0",
        "uvicorn>=0.21.1",
        "pydantic>=1.10.5",
        "python-dotenv>=1.0.0",
        
        # APEX Dependencies
        "sqlalchemy>=2.0.0",
        "pydantic-settings>=2.0.0",
        
        # Aggregator Dependencies (to be updated based on AggreGator's requirements)
        "requests>=2.28.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "mkdocs>=1.4.0",
            "mkdocs-material>=9.0.0",
        ],
    },
    python_requires=">=3.9",
    author="Your Name",
    author_email="your.email@example.com",
    description="NexusCore - Integration hub for APEX and AggreGator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nexuscore",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
