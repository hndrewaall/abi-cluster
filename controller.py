#! /usr/bin/env python

import boto3
import click
import datetime

from botocore.errorfactory import ClientError


class S3LockFilesDontExist(Exception):
    pass


class S3Lock():
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
    
    def __init__(self, s3_client, process_num: str, bucket: str, namespace: str = None, wait_time_s: int = 1, verbose: bool = False):
        self.s3_client = s3_client
        self.process_num = process_num
        self.bucket = bucket
        self.verbose = verbose
        self.namespace = namespace
        if namespace is not None:
            self.FLAG_0_FILE = f"{namespace}{self.FLAG_0_FILE}"
            self.FLAG_1_FILE = f"{namespace}{self.FLAG_1_FILE}"
            self.TURN_FILE = f"{namespace}{self.TURN_FILE}"

    @classmethod
    def init_a_lock(cls, s3_client, bucket, namespace: str = None, overwrite: bool = False, verbose: bool = False):
        return cls(
            s3_client=s3_client,
            process_num="0", # choose something random - it doesn't matter
            bucket=bucket,
            namespace=namespace,
            verbose=verbose,
        ).init()

    def init(self, overwrite: bool = False):
        files = [
            self.FLAG_0_FILE,
            self.FLAG_1_FILE,
            self.TURN_FILE,
        ]
        
        for lock_file in files:
            if overwrite or not self._s3_object_exists(self.FLAG_0_FILE):
                self._write_s3_object(self.FLAG_0_FILE, self.FLAG_UNSET_VALUE)
                if verbose:
                    print(f"Wrote file '{lock_file}'.")
            else:
                if verbose:
                    print(f"Not writing file '{lock_file}' - overwrite false and file exists.")

    def wait_for_lock(self: str):
        if not self._all_files_exist:
            if self.verbose:
                print("Lock files need to be initialized")
            raise S3LockFilesDontExist()
        
        if self.verbose:
            print(f"I am the mighty process {self.process_num}!")
            print(f"Setting {self._my_flag_file} flag and setting turn to {self._their_turn_value}.")

        self._signal_i_want_to_enter()
        self._give_them_their_turn()

        started = datetime.datetime.now()
        
        while self._they_want_to_enter and self._its_their_turn:

            if self.verbose:
                waited_for = (datetime.datetime.now() - started).seconds
                print(f"Poor little old me, process {self.process_num}, waiting for my turn for {waited_for} seconds..")

            # I wait :(
            time.sleep(self.wait_time_s)

        # My turn! Woooooooooooooo
        if self.verbose:
            print(f"Acquired lock for process {self.process_num}!")
    
    @property
    def _signal_i_want_to_enter(self):
        self._write_s3_object(self._my_flag_file, self.FLAG_SET_VALUE)

    @property
    def _give_them_their_turn(self):
        self._write_s3_object(self.TURN_FILE, self._their_turn_value)

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

    @property
    def _all_files_exist(self):
        return self._s3_object_exists(self.FLAG_0_FILE) and \
            self._s3_object_exists(self.FLAG_1_FILE) and \
            self._s3_object_exists(self.TURN_FILE)

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

    def _s3_object_exists(self, filename) -> str:
        try:
            s3.head_object(Bucket=self.bucket, Key=self.filename)
        except ClientError:
            return False
        return True


@click.group()
def cli():
    pass


@cli.command()
@click.option("--bucket", "-b", required=True, type=str, help="Bucket")
@click.option("--process-num", "-p", required=True, type=click.Choice(["0", "1"]), help="Process number")
@click.option("--namespace", "-n", required=False, type=str, help="String to prepend lock files with")
@click.option("--verbose", "-v", default=False, is_flag=True)
def acquire_lock(bucket: str, process_num: str, namespace: str = None, verbose: bool = False) -> None:
    """Acquire lock"""

    s3_client = boto3.client("s3")
    S3Lock(
        s3_client=s3_client,
        process_num=process_num,
        bucket=bucket,
        wait_time_s=5,
        namespace=namespace,
        verbose=verbose,
    ).wait_for_lock()


@cli.command()
@click.option("--bucket", "-b", required=True, type=str, help="Bucket")
@click.option("--overwrite", "-v", default=False, is_flag=True, help="Initialize values, even if the lock files already exist")
@click.option("--namespace", "-n", required=False, type=str, help="String to prepend lock files with")
@click.option("--verbose", "-v", default=False, is_flag=True)
def init(bucket: str, overwrite: bool = False, namespace: str = None, verbose: bool) -> None:
    """Initialize lock"""

    if overwrite:
        are_you_sure = input("Are you sure you want to overwrite? This will erase any values that exist. (yes please) ")
        if not are_you_sure == "yes please":
            print("Exiting without initializing.")
            return

    s3_client = boto3.client("s3")
    S3Lock.init_a_lock(
        s3_client=s3_client,
        bucket=bucket,
        overwrite=overwrite,
        namespace=namespace,
        verbose=verbose,
    )


if __name__ == '__main__':
    cli()