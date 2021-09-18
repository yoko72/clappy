from setuptools import setup

# requires = ["requests>=3.2"]


setup(name='clappy',
      version='0.1.0',
      py_modules=['clappy'],
      description="Command line argument parser for pythonic code",
      long_description="""Command Line Argument Parser for PYthonic code.

    given_kwarg1 = clappy.parse("--kwarg1")
    given_kwarg2 = clappy.parse("--kwarg2")
    
You can directly get each given arg.""",
      classifiers=["Topic :: Software Development :: Libraries :: Python Modules",
                   "Development Status :: 4 - Beta"],
      author='Toshiyuki Yokoyama',
      author_email='yokoyamacode@gmail.com',
      url='https://github.com/yoko72/clappy',
      setup_requires=['wheel'],
      # install_requires=requires,
      keywords="command line argument parser"
      )
