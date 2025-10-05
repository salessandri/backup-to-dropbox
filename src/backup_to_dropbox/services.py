import logging
import os
import os.path
import tarfile

from datetime import datetime
from tempfile import TemporaryDirectory, NamedTemporaryFile, TemporaryFile



class BackupService:

    def __init__(self, dropbox_client, backup_name, encryption_service=None):
        self.__dropbox_client = dropbox_client
        self.__base_dir = os.path.join('/', backup_name)
        self.__encryption_service = encryption_service

    def backup_paths(self, paths):
        execution_time = BackupService.now()
        backup_file = self._generate_backup_file(paths)
        filename = '{}.tar.gz'.format(execution_time.strftime(r'%Y-%m-%d-%H%M'))

        if self.__encryption_service is not None:
            backup_file = self.__encryption_service.encrypt(backup_file)
            filename += '.enc'

        logging.info('Uploading backup: %s', self._get_dropbox_path(filename))
        self.__dropbox_client.upload_file(backup_file, self._get_dropbox_path(filename))


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
            for path in filter(lambda p: BackupService.isfile(p) or BackupService.isdir(p), paths):
                logging.debug('Adding path "%s" to backup', path)
                targz_file.add(path)

        return raw_file

    def _get_dropbox_path(self, filename):
        return os.path.join(self.__base_dir, filename)

    @staticmethod
    def now():
        return datetime.now()

    @staticmethod
    def isfile(path):
        return os.path.isfile(path)

    @staticmethod
    def isdir(path):
        return os.path.isdir(path)



class GpgEncryptionService:

    def __init__(self, destination, gpg_api):
        self.__gpg = gpg_api
        self.__dest = destination
        self.__temp_dir = TemporaryDirectory()

    def encrypt(self, fileobj_input):
        logging.info('Encrypting file using GPG encryption to key: %s', self.__dest)
        fileobj_input.seek(0)
        encrypted_file = os.path.join(self.__temp_dir.name, 'encrypted-file')
        try:
            res = self.__gpg.encrypt(fileobj_input,
                                     self.__dest,
                                     output=encrypted_file,
                                     armor=False)
            if not res.ok:
                raise Exception(res.status)
        except Exception as e:
            logging.error('Failed to encrypt backup file: {}'.format(e))
            raise

        fileobj_input.close()
        return open(encrypted_file, 'rb')
