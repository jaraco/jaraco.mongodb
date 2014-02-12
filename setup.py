# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

classifiers = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: Apache Software License
Programming Language :: Python
Topic :: Database
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: OS Independent
"""

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

import sys

__doc__ = """Improved alternative to official mongooplog utility."""
doclines = __doc__.splitlines()

setup(name="mongooplog-alt",
      py_modules=["mongooplog_alt"],
      version="0.4.2",
      author="Aleksey Sivokon",
      author_email="aleksey.sivokon@gmail.com",
      maintainer="Aleksey Sivokon",
      maintainer_email="aleksey.sivokon@gmail.com",
      url = "https://github.com/asivokon/mongooplog-alt",
      download_url="http://github.com/asivokon/mongooplog-alt/archive/0.4.2.tar.gz",
      license="http://www.apache.org/licenses/LICENSE-2.0.html",
      platforms=["any"],
      keywords='mongodb, mongo, oplog, mongooplog',
      description=doclines[0],
      classifiers=filter(None, classifiers.split("\n")),
      long_description=open("README.rst").read(),
      install_requires=['pymongo'],
      entry_points = {
          'console_scripts': [
              'mongooplog-alt = mongooplog_alt:main'
          ]
      },
      package_data={
          'mongooplog-alt': ['README.rst']
      }
)
