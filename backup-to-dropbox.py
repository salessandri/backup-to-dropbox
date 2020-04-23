#!/usr/bin/env python3

import argparse
import io
import logging
import os.path
import shutil
import tarfile
import time

from datetime import datetime
from tempfile import TemporaryFile

import dropbox
from dropbox.files import (CommitInfo, UploadSessionCursor, WriteMode)

class DropboxClient:

    SINGLE_REQ_UPLOAD_SIZE_LIMIT = 150 * 1024 * 1024 # 150MB

    def __init__(self, dbx_api_client):
        self.__dropbox_client = dbx_api_client

    def upload_file(self, file_to_upload, path):
        file_size = self._get_file_size(file_to_upload)
        file_to_upload.seek(0)

        if file_size <= DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT:
            logging.debug('Using single request to upload file')
            self.__dropbox_client.files_upload(file_to_upload.read(), path)
        else:
            logging.debug('Using multi-request upload session for this file')
            session = None
            offset = 0
            chunk = file_to_upload.read(DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT)
            while len(chunk) == DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT:
                if session is None:
                    logging.debug('Initializing upload session')
                    session = self.__dropbox_client.files_upload_session_start(chunk)
                else:
                    logging.debug('Appending to session %s at offset %d',
                                  session.session_id,
                                  offset)
                    self.__dropbox_client.files_upload_session_append_v2(
                        chunk,
                        UploadSessionCursor(session.session_id, offset)
                    )
                offset += len(chunk)
                chunk = file_to_upload.read(DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT)

            logging.debug('Finishing session %s', session.session_id)
            commit_info = CommitInfo(path=path,
                                     mode=WriteMode('add'),
                                     autorename=False)
            self.__dropbox_client.files_upload_session_finish(
                chunk,
                UploadSessionCursor(session.session_id, offset),
                commit_info
            )

    def delete_file(self, path):
        self.__dropbox_client.files_delete_v2(path)

    def list_files(self, folder_path):
        try:
            return [entry.name for \
                    entry in self.__dropbox_client.files_list_folder(folder_path).entries]
        except dropbox.exceptions.ApiError as e:
            folder_list_error = e.error
            if not folder_list_error.is_path():
                raise
            lookup_error = folder_list_error.get_path()
            if lookup_error.is_not_found():
                return []
            raise

    def _get_file_size(self, file_handle):
        current_tell = file_handle.tell()
        file_handle.seek(0, io.SEEK_END)
        size = file_handle.tell()
        file_handle.seek(current_tell, io.SEEK_SET)
        return size



class BackupService:

    def __init__(self, dropbox_client, backup_name):
        self.__dropbox_client = dropbox_client
        self.__base_dir = os.path.join('/', backup_name)

    def backup_paths(self, paths):
        execution_time = datetime.now()
        with self._generate_backup_file(paths) as raw_file:
            raw_file_size = self._get_file_size(raw_file)
            filename = '{}.tar.gz'.format(execution_time.strftime(r'%Y-%m-%d-%H%M'))

            logging.info('Uploading backup: %s', self._get_dropbox_path(filename))
            self.__dropbox_client.upload_file(raw_file, self._get_dropbox_path(filename))


    def cleanup_old_backups(self, max_to_keep):
        current_backups = self.__dropbox_client.list_files(self.__base_dir)

        if len(current_backups) > max_to_keep:
            files_to_delete = len(current_backups) - max_to_keep
            logging.info('Found %d backups: removing the oldes %d',
                         len(current_backups),
                         files_to_delete)
            current_backups.sort()
            for file in current_backups[:files_to_delete]:
                logging.info('Deleting file: %s', self._get_dropbox_path(file))
                self.__dropbox_client.delete_file(self._get_dropbox_path(file))

    def _generate_backup_file(self, paths):
        raw_file = TemporaryFile()
        with tarfile.open(fileobj=raw_file, mode='w:gz') as targz_file:
            for path in filter(lambda p: os.path.isfile(p) or os.path.isdir(p), paths):
                logging.debug('Adding path "%s" to backup', path)
                targz_file.add(path)

        return raw_file

    def _get_dropbox_path(self, filename):
        return os.path.join(self.__base_dir, filename)



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
    parser.add_argument('paths',
                        nargs='+',
                        help='List of paths to include in the backup')

    args = parser.parse_args()
    start_time = time.perf_counter()
    logging.info('Creating Dropbox client')
    dropbox_client = DropboxClient(dropbox.Dropbox(args.api_key, timeout=None))
    backup_service = BackupService(dropbox_client, args.backup_name)
    if args.max_backups is not None:
        logging.info('Performing cleanup of old backups')
        backup_service.cleanup_old_backups(args.max_backups - 1)
    backup_service.backup_paths(args.paths)
    end_time = time.perf_counter()
    logging.info('Backup finished. Time elapsed: %.2f', end_time - start_time)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

    main()
