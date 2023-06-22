# LOCAL release script for stble-operators as multi-arch image. 
# Just to be used on native ARM machines
# From the default repo, it's necessary to change stackable/ubi8-rust-builder to stackable-experimental/ubi8-rust-builder
from argparse import Namespace, ArgumentParser
from subprocess import run
import os
from typing import List, Optional

def parse() -> Namespace:
    parser = ArgumentParser(
        description="Build and publish product images. Requires docker and buildx (https://github.com/docker/buildx)."
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Version for manifest list, default 0.0.0-dev",
        default="0.0.0-dev",
    )
    parser.add_argument(
        "-s",
        "--single",
        help="Build a single operator as multi arch",
    )
    return parser.parse_args()

def main():
    """Generate a Docker bake file from conf.py and build the given args.product images."""
    args = parse()
    if args.single != "":
        operators=[args.single]
    else:
        operators = ["airflow", "commons", "druid", "hbase", "hdfs", "hive", "kafka", "nifi", "opa", "secret", "spark-k8s", "superset", "trino", "zookeeper", "listener"]

    version = args.version
    for operator in operators:
        os.chdir(f'{operator}-operator/')
        # pulling, retagging and pushing existing AMD images   
        run(["docker", "pull", f"docker.stackable.tech/stackable/{operator}-operator:{version}"])
        run(["docker", "tag", f"docker.stackable.tech/stackable/{operator}-operator:{version}", f"docker.stackable.tech/stackable-experimental/{operator}-operator:{version}-amd64"])
        run(["docker", "image", "push", f"docker.stackable.tech/stackable-experimental/{operator}-operator:{version}-amd64"])
        # Build corresponding ARM image with same tag and push to repository
        run(["docker", "buildx", "build", "-f", f"docker/Dockerfile", "-t", f"docker.stackable.tech/stackable-experimental/{operator}-operator:{version}-arm64", "--platform=linux/arm64", "--load", "."]) 
        run(["docker", "image", "push", f"docker.stackable.tech/stackable-experimental/{operator}-operator:{version}-arm64"])
        # Create and push manifest list for every operator
        run(["docker", "manifest", "create", f"docker.stackable.tech/stackable-experimental/{operator}-operator:{version}", "--amend", f"docker.stackable.tech/stackable-experimental/{operator}-operator:{version}-arm64", "--amend", f"docker.stackable.tech/stackable-experimental/{operator}-operator:{version}-amd64"])
        run(["docker", "manifest", "push", f"docker.stackable.tech/stackable-experimental/{operator}-operator:{version}"])
        os.chdir('..')
if __name__ == "__main__":
    main()
