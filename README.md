# Backup To Dropbox

This is a small utility written in python3 that allows generating tar-gzipped backups and upload them to a [Dropbox](https://www.dropbox.com) account.

## Requirements

The only requirements for this tool are: python3 (>= 3.6) and dropbox (>= 10).
The latter can be installed by running:

```
$ pip install -r requirements.txt
```
or:
```
$ pip install dropbox
```

## Usage

### Obtaining an API Key

In order to use this tool a Dropbox API token is needed. To obtain one, an app needs to be created and an OAuth2 token generated for it.
All this can be done with a few clicks thorough Dropbox's web interface.
[In this link](https://www.iperiusbackup.net/en/create-dropbox-app-get-authentication-token/) you can find a step-by-step guide.

**IMPORTANT NOTE:** I **strongly suggest** that you only give permissions to the app to access a single folder. This minimizes the risk of exposing the whole account in case the token gets stolen but also means that all the backups are going to be neatly stored and tucked away in a separate folder.

### Generating a Backup

In order to generate a backup the application takes two required arguments: the backup's name and the list of paths to back up.

The name is used to create a subfolder under the Dropbox's root (or the application's folder root) where all the backups with the same name are going to be stored.

A tar-gzipped file is going to be created with each one of the paths that are given which actually exist.
Both, full and relative paths can be used and they will be added to the tar-gzipped as given.

The file is going to be uploaded with the name `yyyy-mm-dd-HHMM.tar.gz` at the time of the execution if the file already exists, the backup will fail.

### Keeping a max number of backups

One of the features included is the ability to only keep a certain number of backups. This is done by passing the flag `--max-backups` to the program followed by the number of backups to keep.

The application will delete the oldest files in the given backup name folder until the count is the argument passed minus one.
This is done so as to leave space for the backup being currently generated.

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
