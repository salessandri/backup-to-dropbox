# Backup To Dropbox

This is a small utility written in python3 that allows generating tar-gzipped backups and upload them to a [Dropbox](https://www.dropbox.com) account.

## Installing

### Using uv (recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver. To install the tool using uv:

```bash
$ uv pip install backup-to-dropbox
```

Or to install from source:

```bash
$ git clone https://github.com/salessandri/backup-to-dropbox.git
$ cd backup-to-dropbox
$ uv pip install .
```

### Using pip

```bash
$ pip install backup-to-dropbox
```

## Dependencies

The only requirements for this tool are: `python3` (>= 3.6) and `dropbox` (>= 10). Optionally, if you want to encrypt the backups using GPG the `pretty-bad-protocol` is needed too.

## Development

This project uses `pyproject.toml` for package configuration and `uv` for dependency management. To set up a development environment:

```bash
$ uv venv
$ source .venv/bin/activate  # On Windows: .venv\Scripts\activate
$ uv pip install -e .
```

## Usage

### Obtaining an API Key

In order to use this tool a Dropbox API token is needed. To obtain one, an app needs to be created and an OAuth2 token generated for it.
All this can be done with a few clicks thorough Dropbox's web interface.
[In this link](https://www.iperiusbackup.net/en/create-dropbox-app-get-authentication-token/) you can find a step-by-step guide.

**IMPORTANT NOTE:** I **strongly suggest** that you only give permissions to the app to access a single folder. This minimizes the risk of exposing the whole account in case the token gets stolen but also means that all the backups are going to be neatly stored and tucked away in a separate folder.

### Generating a backup

In order to generate a backup the application takes two required arguments: the backup's name and the list of paths to back up.

The name is used to create a subfolder under the Dropbox's root (or the application's folder root) where all the backups with the same name are going to be stored.

A tar-gzipped file is going to be created with each one of the paths that are given which actually exist.
Both, full and relative paths can be used and they will be added to the tar-gzipped as given.

The file is going to be uploaded with the name `yyyy-mm-dd-HHMM.tar.gz` at the time of the execution if the file already exists, the backup will fail.

### Keeping a max number of backups

One of the features included is the ability to only keep a certain number of backups. This is done by passing the flag `--max-backups` to the program followed by the number of backups to keep.

The application will delete the oldest files in the given backup name folder until the count is the argument passed minus one.
This is done so as to leave space for the backup being currently generated.

### Encrypting the backup

Currently, it is supported to encrypt the generated backup using GPG targeting a particular key.
In order to use this, the public key needs to be already located in a `gpg` compatible keyring in the host.

The following arguments are used to enable the encryption:

 - `--gpg-encrypt <KEY_FINGERPRINT>`: This enables the encryption and sets the key to use for encryption.
 - `--gpg-home <GNUPG_HOME>` _(optional, default: platform dependent)_: If set, it uses the path given as the gnupg home folder.
 - `--gpg-pubkeyring <PUBKEYRING_FILE>` _(optional, default: `pubring.gpg`)_: If set, it uses the file given as the public key-ring.

When encrypting the backup the filename generated will have the `.enc` extension.

To decipher the backup, in a host where the secret key is located run:

```
$ cat 2020-05-01-2300.tar.gz.enc | gpg --decrypt > 2020-05-01-2300.tar.gz
```

### Example

```
$ ./backup-to-dropbox.py --api-key <api-key> --backup-name myserver1-logs --max-backups 10 /var/log/
```

Generates a backup of the `/var/log` folder and uploads it under `[Apps/theappyouregistered]/myserver1-logs/yyyy-mm-dd-HHMM.tar.gz`.
Only the last 10 backups are kept.

## Details

If the backup is not larger than 150MB, a single request is used to upload the file.
In case the file to upload is larger, a multi-request session where each request will upload a 150MB chunk.
Uploading a file larger than 350GB is not possible, this is a Dropbox limitation.

## License

[MIT](https://tldrlegal.com/license/mit-license)
