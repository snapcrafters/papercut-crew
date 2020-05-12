#!/usr/bin/env python3

import subprocess
from functools import wraps
import pathlib
import yaml

import click
import github3
import requests

SECTIONS = [
    #    "art-and-design",
    #    "books-and-reference",
    #    "development",
    #    "devices-and-iot",
    #    "education",
    #    "entertainment",
    "featured",
    #    "finance",
    #    "games",
    #    "health-and-fitness",
    #    "music-and-audio",
    #    "news-and-weather",
    #    "personalisation",
    #    "photo-and-video",
    #    "productivity",
    #    "science",
    #    "security",
    #    "server-and-cloud",  # Doesn't contain any desktop apps
    #    "social",
    #    "utilities",
]


def get_features_apps() -> list:
    apps = set()
    for section in SECTIONS:
        output = subprocess.check_output(
            ["snap", "find", f"--section={section}"], universal_newlines=True)
        for line in output.split("\n")[1:]:
            if line:
                snap_name = line.split()[0]
                apps.add(snap_name)
    return list(apps)


def get_app_info(name: str) -> (dict):
    output = subprocess.check_output(
        ["snap", "info", name], universal_newlines=True)
    return yaml.safe_load(output)





def authenticate(url, token):
    click.secho("# URL: '{}'".format(url), fg="green")

    if not token:
        username = click.prompt("{} Username".format(url))
        password = click.prompt("{} Password".format(url), hide_input=True)
    else:
        username = ""
        password = ""

    if not url.startswith("http"):
        url = "https://" + url
    if "github.com" in url:
        gh = github3.github.GitHub(
            token=token,
            username=username,
            password=password)
    else:
        gh = github3.github.GitHubEnterprise(
            url,
            token=token,
            username=username,
            password=password)
    return gh



def get_issue(gh, name):
    issues = gh.search_issues(f'repo:snapcrafters/papercuts-crew in:title "{name}"')
    for issue in issues:
        if issue.title == name:
            return issue
    return None


def needs_auth(f):
    @wraps(f)
    @click.option(
        '--url', '-u',
        help='URL to Github instance. Defaults to github.com.',
        default="https://github.com")
    @click.option(
        '--token', '-t',
        help='Github authentication token.')
    @click.pass_context
    def wrapper(ctx, *args, url=None, token=None, **kwargs):
        ctx.obj['gh'] = authenticate(url, token)
        return f(*args, **kwargs)
    return wrapper


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = {}


@cli.command()
@click.pass_context
@needs_auth
def create_issues(ctx):
    """create_issues function"""
    apps = get_features_apps()
    click.secho(f"{len(apps)} apps: {apps}")
    with open(pathlib.Path(__file__).parent.absolute() / ".." / ".github" / "ISSUE_TEMPLATE" / "app-report.md") as f:
        template = f.read()

    # Remove the header of the template
    template = template.split("\n", 8)[8]

    gh = ctx.obj['gh']

    for name in apps:
        if get_issue(gh, name):
            print(f"Issue for {name} already exists")
            continue
        else:
            print(f"Creating issue for {name}")
            info = get_app_info(name)
            body = template.format(
                name=name,
                store_url=info['store-url'],
                contact=info.get('contact'),
                # title=info.get('title', ""),
            )
            repo = gh.repository("snapcrafters", "papercuts-crew")
            repo.create_issue(name, body=body, labels=["needs-testing", "app"])



if __name__ == "__main__":
    cli()  # pylint: disable=E1123,E1120
