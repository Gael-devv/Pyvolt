from setuptools import setup
import re

requirements = []
with open('requirements.txt') as f:
  requirements = f.read().splitlines()

version = ''
with open('pyvolt/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

readme = ''
with open('README.md') as f:
    readme = f.read()

extras_require = {
    "speedups": [
        "ujson", 
        "aiohttp[speedups]>=3.6.0,<3.9.0"
    ],
}

packages = [
    'pyvolt',
    'pyvolt.types'
]

setup(name="Pyvolt",
      version=version,
      packages=packages,
      license="MIT",
      author="Gael-devv",
      author_email="gaelp.dev@gmail.com",
      url="https://github.com/Gael-devv/Pyvolt",
      project_urls={
        # "Documentation": "",
        "Issue tracker": "https://github.com/Gael-devv/Pyvolt/issues",
      },
      description="A Python wrapper for the Revolt API",
      long_description=readme,
      long_description_content_type="text/markdown",
      include_package_data=True,
      install_requires=requirements,
      extras_require=extras_require,
      python_requires='>=3.8.0',
      classifiers=[
        "License :: OSI Approved :: MIT License",
        
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
      ]
)
