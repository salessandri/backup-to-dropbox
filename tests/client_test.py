import io
import unittest

from unittest.mock import Mock, call

from dropbox.exceptions import ApiError
from dropbox.file_properties import LookupError
from dropbox.files import (CommitInfo, UploadSessionCursor, WriteMode)

from backup_to_dropbox.clients import DropboxClient



class DropboxClientTest(unittest.TestCase):
    def setUp(self):
        self.api_mock = Mock()
        self.dropbox_client = DropboxClient(self.api_mock)

    def test_file_deletion(self):
        file_to_delete = '/test/file/to/delete'
        self.dropbox_client.delete_file(file_to_delete)
        self.api_mock.files_delete_v2.assert_called_once_with(file_to_delete)

    def test_listing_files_on_empty_folder(self):
        folder_path = '/test/'

        api_call_result = Mock(entries=[])

        self.api_mock.files_list_folder = Mock(return_value=api_call_result)
        files_found = self.dropbox_client.list_files(folder_path)
        self.assertEqual([], files_found)
        self.api_mock.files_list_folder.assert_called_once_with(folder_path)

    def test_listing_files_on_folder_with_files(self):
        folder_path = '/test/'

        file_1 = Mock()
        file_1.configure_mock(name='2020-01')
        file_2 = Mock()
        file_2.configure_mock(name='2020-02')

        api_call_result = Mock(entries=[file_1, file_2])
        expected_files_found = ['2020-01', '2020-02']

        self.api_mock.files_list_folder = Mock(return_value=api_call_result)
        files_found = self.dropbox_client.list_files(folder_path)
        self.assertEqual(expected_files_found, files_found)
        self.api_mock.files_list_folder.assert_called_once_with(folder_path)

    def test_listing_files_on_non_existing_folder(self):
        folder_path = '/test/'

        lookup_error = LookupError.not_found
        folder_error = Mock()
        folder_error.is_path = Mock(return_value=True)
        folder_error.get_path = Mock(return_value=lookup_error)
        not_found_error = ApiError(request_id='1',
                                   error=folder_error,
                                   user_message_text=None,
                                   user_message_locale=None)

        self.api_mock.files_list_folder = Mock(side_effect=not_found_error)
        files_found = self.dropbox_client.list_files(folder_path)
        self.assertEqual([], files_found)
        self.api_mock.files_list_folder.assert_called_once_with(folder_path)

    def test_listing_files_other_error_is_propagated(self):
        folder_path = '/test/'

        non_folder_error = Mock()
        non_folder_error.is_path = Mock(return_value=False)
        not_found_error = ApiError(request_id='1',
                                   error=non_folder_error,
                                   user_message_text=None,
                                   user_message_locale=None)

        self.api_mock.files_list_folder = Mock(side_effect=not_found_error)
        self.assertRaises(ApiError, self.dropbox_client.list_files, folder_path)
        self.api_mock.files_list_folder.assert_called_once_with(folder_path)

    def test_upload_small_file_single_request(self):
        file_path = '/test/12345'
        file_contents = 'abcdefg'
        file_mock = Mock()
        file_mock.tell = Mock(side_effect=[15, DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT])
        file_mock.read = Mock(return_value=file_contents)

        self.dropbox_client.upload_file(file_mock, file_path)
        self.api_mock.files_upload.assert_called_once_with(file_contents, file_path)
        file_mock.seek.assert_called_with(0)

    def test_upload_big_file_multiple_requests(self):
        session_id = Mock(session_id='12345')
        file_path = '/test/12345'
        file_chunks = [
            'a' * DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT,
            'b' * DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT,
            'c'
        ]
        file_mock = Mock()
        file_mock.tell = Mock(side_effect=[15, DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT * 2 + 1])
        file_mock.read = Mock(side_effect=file_chunks)

        self.api_mock.files_upload_session_start.return_value = session_id
        self.dropbox_client.upload_file(file_mock, file_path)

        self.api_mock.files_upload_session_start.assert_called_once_with(file_chunks[0])
        self.api_mock.files_upload_session_append_v2.assert_has_calls([
            call(file_chunks[1],
                 UploadSessionCursor('12345', DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT))
        ])
        self.api_mock.files_upload_session_finish.assert_has_calls([
            call(file_chunks[2],
                 UploadSessionCursor('12345', DropboxClient.SINGLE_REQ_UPLOAD_SIZE_LIMIT * 2),
                 CommitInfo(path=file_path,
                            mode=WriteMode('add'),
                            autorename=False))
        ])
        file_mock.seek.assert_called_with(0)

