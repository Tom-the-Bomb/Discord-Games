import setuptools
import re

requirements = []
version = ''

with open('requirements.txt') as r:
    requirements = r.read().splitlines()

with open("Discord_Games/__init__.py") as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setuptools.setup(
    name="Discord_Games", 
    author="Tom-the-Bomb", 
    version= version, 
    description="A library to help users easily implement games within their discord bot",
    long_description=open("README.md").read(),
    long_description_content_type = "text/markdown",
    license="MIT",
    url="https://github.com/Tom-the-Bomb/Discord-Games",
    project_urls={
        "Repository": "https://github.com/Tom-the-Bomb/Discord-Games",
        "Issue tracker": "https://github.com/Tom-the-Bomb/Discord-Games/issues",
    },
    classifiers=[
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
    include_package_data=True,
    package_data={
        '': ['assets/**']
    },
    packages=[
        'Discord_Games', 
        'Discord_Games.button_games'
    ],
    install_requires=requirements,
    zip_safe=True,
    python_requires='>=3.7'
)