

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="backup-to-dropbox",
    version="0.2.0",
    packages=find_packages(),
    scripts=["backup-to-dropbox.py"],

    install_requires=[
        "dropbox==12.0.2",
        "pretty-bad-protocol==3.1.1",
    ],

    author="Santiago Alessandri",
    author_email="backup-to-dropbox@salessandri.name",
    description="Tool to generate backups (tar.gz files) and upload them to Dropbox",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="backup dropbox",
    url="https://github.com/salessandri/backup-to-dropbox",
    classifiers=[
        "Development Status :: 4 - Beta",

        "Topic :: System :: Archiving :: Backup",
        "Topic :: Utilities",

        "License :: OSI Approved :: MIT License"
    ]
)
