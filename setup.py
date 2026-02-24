"""
Setup para instalação do projeto automatizarBranch.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Ler README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Ler requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip()
        for line in requirements_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="automatizar-branch",
    version="2.0.0",
    description="Aplicativo GUI para automação de branches Git",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jean Heberth Souza Vieira dos Santos",
    author_email="jean.heberth@example.com",
    url="https://github.com/JeanHeberth/automatizarBranch",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "pylint>=3.0.3",
        ]
    },
    entry_points={
        "console_scripts": [
            "git-automation=main:MainWindow",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    keywords="git automation tkinter gui branch management",
    project_urls={
        "Bug Reports": "https://github.com/JeanHeberth/automatizarBranch/issues",
        "Source": "https://github.com/JeanHeberth/automatizarBranch",
    },
)

