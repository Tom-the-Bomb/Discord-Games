from   setuptools import setup
import re

with open("Discord_Games/__init__.py") as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
    name         = "Discord_Games", 
    author       = "Tom-the-Bomb", 
    version      = version, 
    description  = "A library to help users easily implement games within their discord bot",
    long_description              = open("README.md").read(),
    long_description_content_type = "text/markdown",
    license      = "MIT",
    url          = "https://github.com/Tom-the-Bomb/Discord-Games",
    project_urls = {
        "Repository"   : "https://github.com/Tom-the-Bomb/Discord-Games",
        "Issue tracker": "https://github.com/Tom-the-Bomb/Discord-Games/issues",
    },
    classifiers  = [
        "Intended Audience :: Developers",
        'Programming Language :: Python',
        'Natural Language :: English',
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    include_package_data = True,
    packages             = ['Discord_Games'],
    install_requires     = ['discord.py', 'english-words', 'chess', 'akinator.py', 'Pillow',],
    zip_safe        = True,
    python_requires = '>=3.7'
)