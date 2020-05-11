
import unittest

from unittest.mock import Mock, call, ANY

from backup_to_dropbox.services import GpgEncryptionService

class GpgEncryptionServiceTest(unittest.TestCase):
    def setUp(self):
        self.destination = 'TARGET_DESTINATION'
        self.gnupg_mock = Mock()
        self.encryption_service = GpgEncryptionService(self.destination, self.gnupg_mock)

    def test_successful_encryption(self):
        file_to_encrypt = Mock()
        encrypted_file_contents = b'encrypted value'

        def encrypt_file(file_in, target, output, armor):
            with open(output, 'wb') as file_out:
                file_out.write(encrypted_file_contents)
            return Mock(ok=True)

        self.gnupg_mock.encrypt.side_effect = encrypt_file

        file_out = self.encryption_service.encrypt(file_to_encrypt)
        file_out.seek(0)
        content = file_out.read()
        self.assertEqual(encrypted_file_contents, content)
        file_out.close()

        self.gnupg_mock.encrypt.assert_called_once_with(file_to_encrypt,
                                                        self.destination,
                                                        output=ANY,
                                                        armor=False)

    def test_fail_to_encrypt_raises_error(self):
        file_to_encrypt = Mock()

        self.gnupg_mock.encrypt.return_value = Mock(ok=False, status='Could not encrypt')

        self.assertRaises(Exception, self.encryption_service.encrypt, file_to_encrypt)

        self.gnupg_mock.encrypt.assert_called_once_with(file_to_encrypt,
                                                        self.destination,
                                                        output=ANY,
                                                        armor=False)

