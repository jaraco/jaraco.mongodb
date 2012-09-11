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
Operating System :: Unix
"""

from distutils.core import setup
import sys

__doc__ = """\
Improved alternative to official mongooplog utility."

Polls operations from the replication oplog of a remote server, and applies
them to the local server. This capability supports certain classes of real-time
migrations that require that the source server remain online and in operation
throughout the migration process.
"""
doclines = __doc__.splitlines()

setup(name="mongooplog-alt",
      version="0.1.0-dev",
      maintainer="Aleksey Sivokon",
      maintainer_email="aleksey.sivokon@gmail.com",
      url = "https://github.com/silver-/mongooplog-alt",
      license="http://www.apache.org/licenses/LICENSE-2.0.html",
      platforms=["any"],
      description=doclines[0],
      classifiers=filter(None, classifiers.split("\n")),
      long_description="\n".join(doclines[2:]),
      install_requires=['pymongo'],
      entry_points = {
          'console_scripts': [
              'mongooplog-alt = mongooplog_alt:main'
          ]
      }
)
