"""Tasks to set up ubermag for development."""
import contextlib
import os
import shutil

from invoke import task


REPODIR = 'repos'

# order is important
REPOLIST = [
    'ubermagutil',
    'discretisedfield',
    'ubermagtable',
    'micromagneticmodel',
    'micromagneticdata',
    'micromagnetictests',
    'oommfc',
    'mag2exp',
    'ubermag',
]

EXTRA_REPOS = [
    'help',
    'mumax3c',
    'ubermag.github.io',
    'workshop',
]


@task(help={'protocol': 'Protocol to use, either "ssh" or "https".'})
def clone(c, protocol):
    """Clone all repositories."""
    _clone_repos(c, protocol, REPOLIST)


@task(help={'protocol': 'Protocol to use, either "ssh" or "https".'})
def clone_extras(c, protocol):
    """Clone extra repositories.

    Clones the following additional repositories that are part of Ubermag:
    - help
    - mumax3c
    - ubermag.github.io (website repository)
    - workshop
    """
    _clone_repos(c, protocol, EXTRA_REPOS)


@task
def pull(c):
    """Pull changes for all repositories."""
    _execute_command(c, 'git pull')


@task
def install(c):
    """Install all packages in development mode.

    Installs all Ubermag packages with additional development dependencies
    using pip.

    WARNING: Installs into the current environment without any tests.
    """
    _execute_command(c, 'pip install -e .[dev,test]')


@task
def uninstall(c):
    """Uninstall all ubermag subpackages."""
    for pkg in reversed(REPOLIST):
        c.run(f'pip uninstall {pkg} -y')


@task
def init_pre_commit(c):
    """Initialise pre-commit for all subpackages."""
    _execute_command(c, 'pre-commit install')


@task(
    help={
        'repos': 'List of repos to update; all are updated if not specified',
        'files': 'List of files to update; all are updated if not specified',
        'push': 'Push changes; defaults to false',
        'pr': ('Use a dedicated branch (repo-metadata); useful to create a PR'
               'defaults to true')},
    iterable=['files', 'repos']
)
def update_repo_metadata(c, repos, files, push=False, pr=True):
    """Update repo-metadata locally.

    The option ``pr`` uses the branch repo-metadata. If specified the function
    switches to that branch (creates it if necessary) and aplies all changes
    there. It does NOT switch back to the previous branch.
    """
    from repometadata.repometadata import generate_files
    if len(files) == 0:
        files = ['all']
    if len(repos) == 0:
        repos = REPOLIST

    with _change_directory('repometadata'):
        for repo in repos:
            print(f'repo {repo} ...')
            generate_files(
                repository=repo,
                files=files,
                pyproject_path=f'../{REPODIR}/{repo}/pyproject.toml')

            shutil.copytree(src=f'{repo}',
                            dst=f'../{REPODIR}/{repo}',
                            dirs_exist_ok=True)

            with _change_directory(f'../{REPODIR}/{repo}'):
                if pr:
                    c.run('git checkout -b repo-metadata')
                c.run('git commit -m "Update repo metadata."')
                if push:
                    print('push... [COMMENTED OUT]')
                    c.run('git push -u origin')


def _clone_repos(c, protocol, repolist):
    os.makedirs(REPODIR, exist_ok=True)
    if protocol == 'ssh':
        base_url = 'git@github.com:ubermag/'
    elif protocol == 'https':
        base_url = 'https://github.com/ubermag/'
    else:
        raise ValueError(f'Unknown protocol {protocol}.')
    with _change_directory(REPODIR):
        for repo in repolist:
            c.run(f'git clone {base_url}{repo}.git')


def _execute_command(c, cmd):
    for repo in REPOLIST:
        with _change_directory(f'{REPODIR}/{repo}'):
            c.run(cmd)


@contextlib.contextmanager
def _change_directory(path):
    prev_path = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_path)
