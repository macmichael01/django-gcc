django-gcc (Django Google Closure Compiler) is an easy way to compress 
JavaScript files on the fly.

The project is based largely on David Ziegler's Django-css but without the css.
This project uses the Google Closure Compiler and supports making API requests 
or downloading and the compile.jar file and placing in somewhere accessible.

At some point, I would like to add this back into django-css.

Requirements::

BeautifulSoup
Google Closure Compiler (http://code.google.com/closure/compiler/)(optional)

Installation::

sudo python setup.py install

or

place django_gcc somewhere along your python path.

Useage
******

settings::

`OUTPUT_DIR` - default: 'CACHE'
  name of the directory to output JavaScript to.

`COMPRESS` default: opposite of DEBUG
  turns on or off the compressor.

`COMPRESS_JS_FILTERS` default: ['django_gcc.filters.google_closure.GoogleClosureCompilerFilter']
  A list of filters that will be applied to javascript.

`GCC_API_ENABLED` default: False
  Make a request to google's closure compiler.

`GCC_BINARY` default: `java -jar compiler.jar`
  Path to the compiler.jar file (for local compiling)

`GCC_ARGUMENTS` deafault: {}
  arguments that can be passed to the compiler. When using the API, the only
  argument that can be passed is compilation_level. When using the 
  google closure compiler locally refer to the compiler help for a 
  full list of arguments: java -jar compiler.jar --help

Syntax::

    {% load djangogcc %}
    {% djangogcc %}
    	<html of inline or linked JS>
    {% enddjangogcc %}

Examples::

	{% load djangogcc %}
    {% djangogcc %}
    	<script src="/media/js/base.js" type="text/javascript"></script>
    	<script type="text/javascript">var value = "Hello world";</script>
    {% enddjangogcc %}

Which would be rendered to something like::

    <script type="text/javascript" src="/media/CACHE/js/3f33b9146e12.js"></script>

Tips::

- Make sure that your code is safe for the Google Closure Compiler or you might not
get back your expected results.
- If you are a textmate user, be sure to use the JavaScript plugin that will 
indicate whether there are errors or warnings upon saving the JavaScript file. 

Known Issues::

- Some frameworks such as jquery are not safe to run through django_gcc unless
modifications are made to make them safe.