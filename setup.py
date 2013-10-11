from distutils.core import setup
setup(name='mediawiki_client',
      version='0.1',
      author='Pawel Suwala',
      author_email='pawel.suwala@fsfe.org',
      license='GPLv3',
      url='http://suwala.eu',
      packages=['mediawiki_client'],
      scripts = ["wiki_client"],
      description='Mediawiki terminal client',
      long_description = """\
Script for managing your own mediawiki installation.
Allows you to quickly find/add/remove your notes""",
      classifiers = ['Development Status :: 0.1 - Beta',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'Intended Audience :: System Administrators',
                     'License :: GPL License',
                     'Natural Language :: English',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Topic :: Internet :: WWW/HTTP',
                     ],
      requires=['twill (>=0.9)', 'BeautifulSoup (>=3.0)'],

      )
