#! /usr/bin/env python

import boto3
import click


def write_s3_object(client, s3_path: str, data: str) -> None:
    path_components = s3_path.split("/")
    assert len(path_components) == 2
    bucket = path_components[0]
    path = path_components[1]

    result = client.put_object(
        Body=data,
        Bucket=bucket,
        Key=path,
    )
    assert result["ResponseMetadata"]["HTTPStatusCode"] == 200


@click.group()
def cli():
    pass


@cli.command()
def acquire_lock() -> None:
    """Acquire lock"""

    s3_client = boto3.client("s3")
