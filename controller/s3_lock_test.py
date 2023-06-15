import unittest

from botocore.errorfactory import ClientError
from mock import MagicMock
from s3_lock import S3Lock, S3LockFilesDontExist


class MockS3Client():
    def __init__(self):
        self.s3_client = MagicMock()
        
        self.file_exists = {}
        self.put_return_status = {}
        self.get_return_status = {}
        self.get_return_data = {}

        def head_object(Bucket, Key):
            if not self.file_exists[Key]:
                raise ClientError()
            
        def put_object(Body, Bucket, Key):
            return {
                "ResponseMetadata": {
                    "HTTPStatusCode": self.put_return_status[Key]
                }
            }

        def get_object(Bucket, Key):
            return {
                "Body": MagicMock().read = lambda: self.get_return_data[Key]
                "ResponseMetadata": {
                    "HTTPStatusCode": self.get_return_status[Key]
                }
            }

        self.s3_client.head_object = head_object
        self.s3_client.put_object = put_object
        self.s3_client.get_object = get_object

    def set_file_exists(self, filename: str, exists: bool):
        self.file_exists[filename] = exists
        
    def set_put_return_status(self, filename: str, status: int):
        self.put_return_status[filename] = status
        
    def set_get_return_status_and_data(self, filename: str, status: int, value: str):
        self.get_return_status[filename] = status
        self.get_return_data[filename] = status


class TestS3Lock(unittest.TestCase):

    def test_simple_working_case(self):
        s3_client = MockS3Client(default_exists=True)

        s3_client.set_file_exists(S3Lock.FLAG_0_FILE, True)
        s3_client.set_file_exists(S3Lock.FLAG_1_FILE, True)
        s3_client.set_file_exists(S3Lock.TURN_FILE, True)

        s3_client.set_put_return_status(S3Lock.FLAG_0_FILE, 200)
        s3_client.set_put_return_status(S3Lock.FLAG_1_FILE, 200)
        s3_client.set_put_return_status(S3Lock.TURN_FILE, 200)

        s3_client.set_get_return_status_and_data(S3Lock.FLAG_0_FILE, 200, S3Lock.FLAG_UNSET_VALUE)
        s3_client.set_get_return_status_and_data(S3Lock.FLAG_1_FILE, 200, S3Lock.FLAG_UNSET_VALUE)
        s3_client.set_get_return_status_and_data(S3Lock.TURN_FILE, 200, S3Lock.P0_TURN_VALUE)

        s3_lock = S3Lock(s3_client=s3_client, bucket="", process_num=S3Lock.PROCESS_0)
        s3_lock.wait_for_lock()


if __name__ == '__main__':
    unittest.main()