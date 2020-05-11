#!/usr/bin/env python3

import argparse
import logging
import time

import dropbox

from backup_to_dropbox.clients import DropboxClient
from backup_to_dropbox.services import BackupService, GpgEncryptionService



def main():
    parser = argparse.ArgumentParser(description='Backup data using Dropbox as storage.')
    parser.add_argument('--api-key',
                        required=True,
                        help='Dropbox API Key to use for authentication')
    parser.add_argument('--backup-name',
                        required=True,
                        help='Name for the backup in Dropbox')
    parser.add_argument('--max-backups',
                        type=int,
                        help='Max number of these backups to keep in Dropbox')
    parser.add_argument('--gpg-encrypt',
                        help='Key fingerprint to use for encrypting')
    parser.add_argument('--gpg-home',
                        help='Folder to use as GPG home')
    parser.add_argument('--gpg-pubkeyring',
                        help='GPG public key keyring to use')
    parser.add_argument('paths',
                        nargs='+',
                        help='List of paths to include in the backup')

    args = parser.parse_args()
    start_time = time.perf_counter()
    logging.info('Creating Dropbox client')
    dropbox_client = DropboxClient(dropbox.Dropbox(args.api_key, timeout=None))

    encryption_service = None
    if args.gpg_encrypt is not None:
        from pretty_bad_protocol import gnupg

        gnupg_api = gnupg.GPG(homedir=args.gpg_home, keyring=args.gpg_pubkeyring)
        encryption_service = GpgEncryptionService(args.gpg_encrypt, gnupg_api)

    backup_service = BackupService(dropbox_client, args.backup_name, encryption_service)
    if args.max_backups is not None:
        logging.info('Performing cleanup of old backups')
        backup_service.cleanup_old_backups(args.max_backups - 1)
    backup_service.backup_paths(args.paths)
    end_time = time.perf_counter()
    logging.info('Backup finished. Time elapsed: %.2f', end_time - start_time)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    main()
