#! /usr/bin/env python

import boto3
import click
import datetime


class S3LockClient():
    """
    Based on: https://en.wikipedia.org/wiki/Peterson%27s_algorithm
    P0      flag[0] = true;
    P0_gate turn = 1;
            while (flag[1] == true && turn == 1)
            {
                // busy wait
            }
            // critical section
            ...
            // end of critical section
            flag[0] = false;
    P1      flag[1] = true;
    P1_gate turn = 0;
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
    
    def __init__(self, s3_client, process_num: str, bucket: str, wait_time_s: int = 1, verbose: bool = False):
        self.s3_client = s3_client
        self.process_num = process_num
        self.bucket = bucket
        self.verbose = verbose

    def wait_for_lock(self: str):
        if self.verbose:
            print(f"I am the mighty process {self.process_num}!")
            print(f"Setting {self._my_flag_file} flag and setting turn to {self._their_turn_value}.")

        self._write_s3_object(self._my_flag_file, self.FLAG_SET_VALUE)
        self._write_s3_object(self.TURN_FILE, self._their_turn_value)

        started = datetime.datetime.now()
        
        while (self._they_want_to_enter and self._its_their_turn):

            if self.verbose:
                waited_for = (datetime.datetime.now() - started).seconds
                print(f"Poor little old me, process {self.process_num}, waiting for my turn for {waited_for} seconds..")

            # I wait :(
            time.sleep(self.wait_time_s)

        # My turn! Woooooooooooooo
        if self.verbose:
            print(f"Acquired lock for process {self.process_num}!")

    @property
    def _they_want_to_enter(self):
        return self._read_s3_object(self._their_flag_file) == self.FLAG_SET_VALUE

    @property
    def _its_their_turn(self):
        return self._read_s3_object(self.TURN_FILE) == self._their_turn_value

    @property
    def _my_flag_file(self):
        return self.FLAG_0_FILE if self.process_num == "0" else self.FLAG_1_FILE

    @property
    def _their_flag_file(self):
        return self.FLAG_0_FILE if self.process_num == "1" else self.FLAG_1_FILE

    @property
    def _their_turn_value(self):
        return self.P0_TURN_VALUE if self.process_num == "1" else self.P1_TURN_VALUE

    def _write_s3_object(self, filename, data: str) -> None:
        result = self.s3_client.put_object(
            Body=data,
            Bucket=self.bucket,
            Key=filename,
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200

    def _read_s3_object(self, filename) -> str:
        result = self.s3_client.get_object(
            Bucket=self.bucket,
            Key=filename,
        )
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200
        return str(result["Body"].read(), "UTF-8")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--bucket", "-b", required=True, type=str, help="Bucket")
@click.option("--process-num", "-p", required=True, type=click.Choice(["0", "1"]), help="Process number")
@click.option("--verbose", "-v", default=False, is_flag=True)
def acquire_lock(bucket: str, process_num: str, verbose: bool = False) -> None:
    """Acquire lock"""

    s3_client = boto3.client("s3")
    S3LockClient(
        s3_client=s3_client,
        process_num=process_num,
        bucket=bucket,
        wait_time_s=5,
        verbose=verbose,
    ).wait_for_lock()

if __name__ == '__main__':
    cli()