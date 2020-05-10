

from setuptools import setup, find_packages

setup(
    name="BackupToDropbox",
    version="0.2.0",
    packages=find_packages(),
    scripts=["backup-to-dropbox.py"],

    install_requires=[
        "dropbox==10.1.1",
        "pretty-bad-protocol==3.1.1",
    ],

    author="Santiago Alessandri",
    author_email="santiago@salessandri.name",
    description="Tool to generate backups (tar.gz files) and upload them to Dropbox",
    keywords="backup dropbox",
    url="https://github.com/salessandri/backup-to-dropbox",
    classifiers=[
        "Development Status :: 4 - Beta",

        "Topic :: System :: Archiving :: Backup",
        "Topic :: Utilities",

        "License :: OSI Approved :: MIT License"
    ]
)
