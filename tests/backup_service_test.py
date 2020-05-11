import io
import tarfile
import unittest

from datetime import datetime
from unittest.mock import ANY, MagicMock, Mock, call, patch

from backup_to_dropbox.services import BackupService

class BackupServiceTest(unittest.TestCase):

    def setUp(self):
        self.dropbox_client = Mock()
        self.encryption_service = Mock()
        self.backup_name = 'TestBackupName'
        self.backup_service = BackupService(self.dropbox_client,
                                            self.backup_name,
                                            self.encryption_service)

    def test_cleanup_not_needed(self):
        self.dropbox_client.list_files.return_value = [
            '2020-05-02-0000.tar.gz',
            '2020-05-01-0000.tar.gz',
        ]

        self.backup_service.cleanup_old_backups(2)

        self.dropbox_client.list_files.assert_called_once_with('/' + self.backup_name)

    def test_cleanup_deletes_correct_files(self):
        self.dropbox_client.list_files.return_value = [
            '2020-05-02-0000.tar.gz',
            '2020-05-01-0000.tar.gz',
            '2020-05-03-0000.tar.gz',
            '2020-04-03-0000.tar.gz',
        ]

        self.backup_service.cleanup_old_backups(2)

        self.dropbox_client.list_files.assert_called_once_with('/' + self.backup_name)
        self.dropbox_client.delete_file.assert_has_calls([
            call('/{}/2020-04-03-0000.tar.gz'.format(self.backup_name)),
            call('/{}/2020-05-01-0000.tar.gz'.format(self.backup_name)),
        ])

    @patch.object(BackupService, 'now')
    @patch.object(BackupService, 'isfile')
    @patch.object(BackupService, 'isdir')
    @patch('tarfile.open')
    def test_backup_with_encryption(self, open_tarfile_mock, isdir_mock, isfile_mock, date_now):
        backup_path = '/var/log/test'
        date_now.return_value = datetime(2020, 5, 10, 17, 15, 30)

        backup_tar_file = MagicMock()
        open_tarfile_mock.return_value.__enter__.return_value = backup_tar_file
        isfile_mock.return_value = True

        encrypted_file = Mock()
        self.encryption_service.encrypt.return_value = encrypted_file

        self.backup_service.backup_paths([backup_path])

        open_tarfile_mock.assert_called_once()
        isfile_mock.assert_called_once()
        backup_tar_file.add.assert_called_once_with(backup_path)

        self.encryption_service.encrypt.assert_called_once()

        expected_filepath = '/{}/2020-05-10-1715.tar.gz.enc'.format(self.backup_name)
        self.dropbox_client.upload_file.assert_called_once_with(encrypted_file, expected_filepath)

    @patch.object(BackupService, 'now')
    @patch.object(BackupService, 'isfile')
    @patch.object(BackupService, 'isdir')
    @patch('tarfile.open')
    def test_backup_without_encryption(self, open_tarfile_mock, isdir_mock, isfile_mock, date_now):
        self.backup_service = BackupService(self.dropbox_client, self.backup_name)

        backup_path = '/var/log/test'
        date_now.return_value = datetime(2020, 5, 10, 17, 15, 30)

        backup_tar_file = MagicMock()
        open_tarfile_mock.return_value.__enter__.return_value = backup_tar_file
        isfile_mock.return_value = True

        self.backup_service.backup_paths([backup_path])

        open_tarfile_mock.assert_called_once()
        isfile_mock.assert_called_once()
        backup_tar_file.add.assert_called_once_with(backup_path)

        expected_filepath = '/{}/2020-05-10-1715.tar.gz'.format(self.backup_name)
        self.dropbox_client.upload_file.assert_called_once_with(ANY, expected_filepath)

    @patch.object(BackupService, 'now')
    @patch.object(BackupService, 'isfile')
    @patch.object(BackupService, 'isdir')
    @patch('tarfile.open')
    def test_backup_add_existing_elems(self, open_tarfile_mock, isdir_mock, isfile_mock, date_now):
        existing_file = '/var/log/test'
        existing_dir = '/var/log/test_dir'
        non_existing_path = '/var/log/missing'

        def isfile(path):
            if path == existing_file:
                return True
            return False

        def isdir(path):
            if path == existing_dir:
                return True
            return False

        date_now.return_value = datetime(2020, 5, 10, 17, 15, 30)

        backup_tar_file = MagicMock()
        open_tarfile_mock.return_value.__enter__.return_value = backup_tar_file
        isfile_mock.side_effect = isfile

        encrypted_file = Mock()
        self.encryption_service.encrypt.return_value = encrypted_file

        self.backup_service.backup_paths([existing_file, existing_dir, non_existing_path])

        open_tarfile_mock.assert_called_once()
        backup_tar_file.add.assert_has_calls([call(existing_file), call(existing_dir)],
                                             any_order=True)

        self.encryption_service.encrypt.assert_called_once()

        expected_filepath = '/{}/2020-05-10-1715.tar.gz.enc'.format(self.backup_name)
        self.dropbox_client.upload_file.assert_called_once_with(encrypted_file, expected_filepath)



