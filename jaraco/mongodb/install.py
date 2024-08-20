import io
import json
import pathlib
import platform
import posixpath
import re
import sys
import urllib.request
import zipfile

import autocommand
from more_itertools import one

if sys.version_info > (3, 12):
    import tarfile
else:
    from backports import tarfile


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
        ('Windows', 'AMD64'): 'Windows x64',
        ('Windows', 'ARM64'): 'Windows x64',
    }
    plat_name = lookup[(platform.system(), platform.machine())]
    format = 'zip' if 'Windows' in plat_name else 'tgz'
    return platforms[plat_name][format]


class RootFinder(set):
    def __call__(self, info, path):
        self.add(self.root(info.name))
        return info

    @staticmethod
    def root(name):
        root, _, _ = name.partition(posixpath.sep)
        return root

    @classmethod
    def from_names(cls, names):
        return cls(map(cls.root, names))


def _extract_all(resp, target):
    desig = resp.headers['Content-Type'].lower().replace('/', '_').replace('+', '_')
    func_name = f'_extract_{desig}'
    return globals()[func_name](resp, target)


def _extract_application_zip(resp, target):
    data = io.BytesIO(resp.read())
    with zipfile.ZipFile(data) as obj:
        roots = RootFinder.from_names(obj.namelist())
        obj.extractall(target)
    return roots


def _extract_application_gzip(resp, target):
    with tarfile.open(fileobj=resp, mode='r|*') as obj:
        roots = RootFinder()
        # python/typeshed#10514
        obj.extractall(target, filter=roots)  # type: ignore
    return roots


def install(target: pathlib.Path = pathlib.Path()):
    url = get_download_url()
    with urllib.request.urlopen(url) as resp:
        roots = _extract_all(resp, target.expanduser())
    return target.joinpath(one(roots))


autocommand.autocommand(__name__)(install)
