import json
import pathlib
import platform
import re
import tarfile
import urllib.request
import posixpath

import autocommand
from more_itertools import one


def get_download_url():
    source = 'https://www.mongodb.com/try/download/community'
    with urllib.request.urlopen(source) as resp:
        html = resp.read().decode('utf-8')
    server_data = re.search(
        r'<script id="server-data">\s*window\.__serverData=(.*?)\s*</script>',
        html,
        flags=re.DOTALL | re.MULTILINE,
    ).group(1)
    data = json.loads(server_data)
    versions = data['components'][2]['props']['embeddedComponents'][0]['props'][
        'items'
    ][2]['embeddedComponents'][0]['props']['data'][0]['data'][0]
    best_version = next(ver for ver in versions if versions[ver]['meta']['current'])
    platforms = versions[best_version]['platforms']
    lookup = {
        ('Darwin', 'arm64'): 'macOS ARM 64',
        ('Darwin', 'x86_64'): 'macOS x64',
        ('Linux', 'x86_64'): 'Ubuntu 22.04 x64',
        ('Linux', 'aarch64'): 'Ubuntu 22.04 ARM 64',
        ('Windows', 'x86_64'): 'Windows x64',
        ('Windows', 'ARM64'): 'Windows x64',
    }
    plat_name = lookup[(platform.system(), platform.machine())]
    return platforms[plat_name]['tgz']


class RootFinder(set):
    def __call__(self, info, path):
        root, _, _ = info.name.partition(posixpath.sep)
        self.add(root)
        return info


def install(target: pathlib.Path = pathlib.Path()):
    url = get_download_url()
    with urllib.request.urlopen(url) as resp:
        with tarfile.open(fileobj=resp, mode='r|*') as obj:
            roots = RootFinder()
            # python/typeshed#10514
            obj.extractall(target.expanduser(), filter=roots)  # type: ignore
    return target.joinpath(one(roots))


autocommand.autocommand(__name__)(install)
