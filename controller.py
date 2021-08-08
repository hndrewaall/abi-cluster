#! /usr/bin/env python

import boto3
import click


class S3LockClient():
    """
    Based on: https://en.wikipedia.org/wiki/Peterson%27s_algorithm
    P0:      flag[0] = true;
    P0_gate: turn = 1;
            while (flag[1] == true && turn == 1)
            {
                // busy wait
            }
            // critical section
            ...
            // end of critical section
            flag[0] = false;
    P1:      flag[1] = true;
    P1_gate: turn = 0;
            while (flag[0] == true && turn == 0)
            {
                // busy wait
            }
            // critical section
            ...
            // end of critical section
            flag[1] = false;
    """
    FLAG_0_FILE = "flag_0"
    FLAG_1_FILE = "flag_1" 
    TURN_FILE = "turn"
    
    FLAG_SET_VALUE = "1"
    FLAG_UNSET_VALUE = "0"

    P0_TURN_VALUE = "0"
    P1_TURN_VALUE = "1"
    
    def __init__(self, s3_client, process_num: int, bucket: str, verbose: bool = False):
        self.s3_client = s3_client
        self.process_num = process_num
        self.bucket = bucket
        self.verbose = verbose

    def wait_for_lock(self: str):
        write_s3_object(self._my_flag_file, self.FLAG_SET_VALUE)
        write_s3_object(self.TURN_FILE, self._their_turn_value)
        
        while (self._they_want_to_enter and self._its_their_turn):
            time.sleep(1)

    @property
    def _they_want_to_enter(self):
        return self._read_s3_object(self._their_flag_file) == self.FLAG_SET_VALUE

    @property
    def _its_their_turn(self):
        return self._read_s3_object(self.TURN_FILE) == self._their_turn_value

    @property
    def _my_flag_file(self):
        return FLAG_0_FILE if self.process_num == 0 else FLAG_1_FILE

    @property
    def _their_flag_file(self):
        return FLAG_0_FILE if self.process_num == 1 else FLAG_1_FILE

    @property
    def _their_turn_value(self):
        return P0_TURN_VALUE if self.process_num == 1 else P1_TURN_VALUE

    def _write_s3_object(self, filename, data: str) -> None:
        result = self.client.put_object(
            Body=data,
            Bucket=self.bucket,
            Key=filename,
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def _read_s3_object(self, filename) -> str:
        result = self.client.get_object(
            Bucket=self.bucket,
            Key=filename,
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200
        return str(result["Body"].read(), "UTF-8")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--process-num", "-p", required=True, type=click.Choice([0, 1], help="Process number")
def acquire_lock(process_name: str) -> None:
    """Acquire lock"""

    s3_client = boto3.client("s3")

    S3LockClient().wait_for_lock()

