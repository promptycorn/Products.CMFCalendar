import os
from setuptools import setup
from setuptools import find_packages

NAME = 'CMFCalendar'

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'Products', NAME)

def _package_doc(name):
    f = open(os.path.join(package, name))
    return f.read()

_boundary = '\n' + ('-' * 60) + '\n\n'
README = ( _package_doc('README.txt')
         + _boundary
         + _package_doc('CHANGES.txt')
         + _boundary
         + "Download\n========"
         )

setup(name='Products.%s' % NAME,
      version=_package_doc('version.txt').strip(),
      description='Calendar product for the Zope Content Management Framework',
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        ],
      keywords='web application server zope zope2 cmf',
      author="Zope Foundation and Contributors",
      author_email="zope-cmf@zope.org",
      url="http://pypi.python.org/pypi/Products.CMFCalendar",
      license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
      packages=find_packages(),
      include_package_data=True,

      python_requires='>=3.10',
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Zope>=6.1,<7',
          'Products.CMFCore',
          'Products.CMFDefault',
          'Products.GenericSetup',
          'zope.app.form',
          ],
      tests_require=[
          'zope.testing >= 3.7.0',
          'Products.DCWorkflow',
          ],
      extras_require = dict(
          test = ['Products.DCWorkflow', 'zope.testrunner'],
          ),
      test_suite='Products.%s.tests' % NAME,
      entry_points="""
      [zope2.initialize]
      Products.%s = Products.%s:initialize
      """ % (NAME, NAME),
      )
