from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='ospcreator',
      version='0.2',
      description='OpenStack project creator with OpenContrail route targets integration',
      url='http://github.com/stelucz/ospcreator',
      author='Lukas Stehlik',
      license='MIT',
      packages=['ospcreator'],
      entry_points={
          'console_scripts': [
              'ospcreator = ospcreator.__main__:main'
          ]
      },
      install_requires=[
          'pyyaml',
          'python-keystoneclient',
          'python-neutronclient',
          'python-glanceclient',
          'python-cinderclient',
          'python-novaclient',
      ])
