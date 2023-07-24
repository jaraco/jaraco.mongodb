import json
import re
import platform

import requests


def get_download_url():
    html = requests.get('https://www.mongodb.com/try/download/community').text
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


def install():
    print(get_download_url())


__name__ == '__main__' and install()
