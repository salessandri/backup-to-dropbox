import io
import logging

from dropbox.exceptions import ApiError
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
        except ApiError as e:
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
