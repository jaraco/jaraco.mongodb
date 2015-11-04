#!/usr/bin/env python
# Generated by jaraco.develop 2.16
# https://pypi.python.org/pypi/jaraco.develop

import io
import sys

import setuptools

with io.open('README.txt', encoding='utf-8') as readme:
	long_description = readme.read()

needs_pytest = {'pytest', 'test'}.intersection(sys.argv)
pytest_runner = ['pytest_runner'] if needs_pytest else []
needs_sphinx = {'release', 'build_sphinx', 'upload_docs'}.intersection(sys.argv)
sphinx = ['sphinx'] if needs_sphinx else []

setup_params = dict(
	name='jaraco.mongodb',
	use_scm_version=True,
	author="Jason R. Coombs",
	author_email="jaraco@jaraco.com",
	description="Routines and classes supporting MongoDB environments",
	long_description=long_description,
	url="https://github.com/jaraco/jaraco.mongodb",
	packages=setuptools.find_packages(),
	namespace_packages=['jaraco'],
	install_requires=[
		'pymongo',
		'python-dateutil',
		'jaraco.services',
		'portend',
		'jaraco.itertools',
	],
	setup_requires=[
		'setuptools_scm',
	] + pytest_runner + sphinx,
	tests_require=[
		'pytest',
		'cherrypy',
	],
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3",
	],
	entry_points={
		'pytest11': [
			'MongoDB = jaraco.mongodb.fixtures',
		],
	},
)
if __name__ == '__main__':
	setuptools.setup(**setup_params)
