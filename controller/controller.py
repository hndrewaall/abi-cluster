#! /usr/bin/env python

import boto3
import click
from s3_lock import S3Lock


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
@click.option("--process-num", "-p", required=True, type=click.Choice(["0", "1"]), help="Process number")
@click.option("--namespace", "-n", required=False, type=str, help="String to prepend lock files with")
@click.option("--verbose", "-v", default=False, is_flag=True)
def release_lock(bucket: str, process_num: str, namespace: str = None, verbose: bool = False) -> None:
    """Acquire lock"""

    s3_client = boto3.client("s3")
    S3Lock(
        s3_client=s3_client,
        process_num=process_num,
        bucket=bucket,
        wait_time_s=5,
        namespace=namespace,
        verbose=verbose,
    ).release_lock()


@cli.command()
@click.option("--bucket", "-b", required=True, type=str, help="Bucket")
@click.option("--overwrite", "-v", default=False, is_flag=True, help="Initialize values, even if the lock files already exist")
@click.option("--namespace", "-n", required=False, type=str, help="String to prepend lock files with")
@click.option("--verbose", "-v", default=False, is_flag=True)
def init(bucket: str, overwrite: bool = False, namespace: str = None, verbose: bool = False) -> None:
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