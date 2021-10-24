#! /usr/bin/env python

import boto3
import click
from s3_lock import S3Lock


@click.group()
def cli():
    """
    Locking utility for two processes that uses S3 as a backend.

    Example usage:

    \b
    ------- Terminal 0:
    # This creates all the files and marks them as unset (no one has the lock).
    ./controller.py init -b seaucre-abi-test && echo "Init lock ended"
    Init lock ended
    ./controller.py acquire-lock -b seaucre-abi-test -p 0 -v && echo "P0 acquire ended"
    I am the mighty process 0!
    Setting flag_0 and setting turn to 1.
    Acquired lock for process 0!
    P0 acquire ended
    ------- Terminal 1:
    ./controller.py acquire-lock -b seaucre-abi-test -p 1 -v && echo "P1 acquire ended"
    I am the mighty process 1!
    Setting flag_1 and setting turn to 0.
    Poor little old me, process 1, waiting for my turn for 0 seconds..
    Poor little old me, process 1, waiting for my turn for 5 seconds..
    ------- Terminal 0:
    ./controller.py release-lock -b seaucre-abi-test -p 0 -v && echo "Release ended"
    Released lock for process 0!
    Release ended
    ------- Terminal 1:
    Acquired lock for process 1!
    P1 acquire ended
    """
    pass


@cli.command()
@click.option("--bucket", "-b", required=True, type=str, help="Bucket")
@click.option(
    "--process-num",
    "-p",
    required=True,
    type=click.Choice(["0", "1"]),
    help="Process number",
)
@click.option(
    "--namespace",
    "-n",
    required=False,
    type=str,
    help="String to prepend lock files with",
)
@click.option("--verbose", "-v", default=False, is_flag=True)
def acquire_lock(
    bucket: str, process_num: str, namespace: str = None, verbose: bool = False
) -> None:
    """
    \b
    Acquire lock.
    This process will have the lock until release-lock is run.
    """

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
@click.option(
    "--process-num",
    "-p",
    required=True,
    type=click.Choice(["0", "1"]),
    help="Process number",
)
@click.option(
    "--namespace",
    "-n",
    required=False,
    type=str,
    help="String to prepend lock files with",
)
@click.option("--verbose", "-v", default=False, is_flag=True)
def release_lock(
    bucket: str, process_num: str, namespace: str = None, verbose: bool = False
) -> None:
    """Release lock."""

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
@click.option(
    "--overwrite",
    "-v",
    default=False,
    is_flag=True,
    help="If set, will overwrite existing values. This has the effect of releasing the lock on p0 and p1.",
)
@click.option(
    "--namespace",
    "-n",
    required=False,
    type=str,
    help="String to prepend lock files with",
)
@click.option("--verbose", "-v", default=False, is_flag=True)
def init(
    bucket: str, overwrite: bool = False, namespace: str = None, verbose: bool = False
) -> None:
    """
    \b
    Initialize lock.
    That is, create the necessary files, and mark them as unset (no one has the lock).
    Harmless to run twice if --overwrite isn't set.
    """

    if overwrite:
        are_you_sure = input(
            "Are you sure you want to overwrite? This will erase any values that exist. (yes please) "
        )
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


if __name__ == "__main__":
    cli()
