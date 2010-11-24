import os
import re
import subprocess

from BeautifulSoup import BeautifulSoup
from tempfile import NamedTemporaryFile
from textwrap import dedent

from django import template
from django.conf import settings as django_settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.loader import render_to_string

from django_gcc.conf import settings
from django_gcc import filters
from django_gcc.utils import get_hexdigest


register = template.Library()


class UncompressableFileError(Exception):
    pass


def exe_exists(program):

    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return True
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return True
    return False

class Compressor(object):

    def __init__(self, content, ouput_prefix="compressed", xhtml=False, media_url=None):
        from django.contrib.sites.models import Site
        
        self.content = content
        self.ouput_prefix = ouput_prefix
        self.split_content = []
        self.soup = BeautifulSoup(self.content)
        self.xhtml = xhtml
        self.media_url = media_url or settings.MEDIA_URL
        
        try:
          self.domain = Site.objects.get_current().domain
        except:
          self.domain = ''

    def content_hash(self):
        """docstring for content_hash"""
        pass

    def split_contents(self):
        raise NotImplementedError('split_contents must be defined in a subclass')

    def get_filename(self, url):
        if not url.startswith(self.media_url):
            raise UncompressableFileError('"%s" is not in COMPRESS_URL ("%s") and can not be compressed' % (url, self.media_url))
            
        #url = os.path.realpath(url)
        basename = url[len(self.media_url):]
        filename = os.path.join(settings.MEDIA_ROOT, basename)
        
        return os.path.realpath(filename)

    @property
    def mtimes(self):
        return (os.path.getmtime(h[1]) for h in self.split_contents() if h[0] == 'file')

    @property
    def cachekey(self):
        """
        cachekey for this block of css or js.
        """
        cachebits = [self.content]
        cachebits.extend([str(m) for m in self.mtimes])
        cachestr = "".join(cachebits)
        return "%s.django_gcc.%s.%s" % (self.domain, get_hexdigest(cachestr)[:12], settings.COMPRESS)

    @property
    def hunks(self):
        """
        Returns a list of processed data
        """
        if getattr(self, '_hunks', ''):
            return self._hunks
        self._hunks = []
        for kind, v, elem in self.split_contents():
            if kind == 'hunk':
                input = v
                if self.filters:
                    input = self.filter(input, 'input', elem=elem)
                self._hunks.append(input)
            if kind == 'file':
                fd = open(v, 'rb')
                input = fd.read()
                if self.filters:
                    input = self.filter(input, 'input', filename=v, elem=elem)
                self._hunks.append(input)
                fd.close()
        return self._hunks

    def concat(self):
        return "\n".join(self.hunks)

    def filter(self, content, method, **kwargs):        
        for f in self.filters:
            filter = getattr(filters.get_class(f)(content, filter_type=self.type), method)
            try:
                if callable(filter):
                    if method == 'input':
                        content = filter(media_url=self.media_url, **kwargs)
                    if method == 'output':
                        content = filter(content, **kwargs)
            except NotImplementedError:
                pass
        if type(content) == str:
            return content
        else:
            return unicode(content).encode('utf-8')

    @property
    def combined(self):
        if getattr(self, '_output', ''):
            return self._output
        output = self.concat()
        filter_method = getattr(self, 'filter_method', None)
        if self.filters:
            output = self.filter(output, 'output')
        self._output = output
        return self._output

    @property
    def hash(self):
        return get_hexdigest(self.combined)[:12]

    @property
    def new_filepath(self):
        filename = "".join((self.hash, self.extension))
        filepath = "/".join((settings.OUTPUT_DIR.strip('/'), self.ouput_prefix, filename))
        return filepath

    def save_file(self):
        if default_storage.exists(self.new_filepath):
            return False
        default_storage.save(self.new_filepath, ContentFile(self.combined))
        return True

    def return_compiled_content(self, content):
        """
        Return compiled content
        """
        return content
        
    def output(self):
        """
        Return the versioned file path if COMPRESS = True
        """
        if not settings.COMPRESS:
            return self.return_compiled_content(self.content)
        
        url = "/".join((self.media_url.rstrip('/'), self.new_filepath))
        self.save_file()
        
        context = getattr(self, 'extra_context', {})
        
        context['url'] = url
        context['xhtml'] = self.xhtml
        
        return render_to_string(self.template_name, context)

    
class JsCompressor(Compressor):

    def __init__(self, content, ouput_prefix="js", xhtml=False, media_url=None):
        self.extension = ".js"
        self.template_name = "django_gcc/js.html"
        self.filters = settings.COMPRESS_JS_FILTERS
        self.type = 'js'
        super(JsCompressor, self).__init__(content, ouput_prefix, xhtml, media_url)

    def split_contents(self):
        """ Iterates over the elements in the block """
        if self.split_content:
            return self.split_content
            
        split = self.soup.findAll('script')
        for elem in split:
            if elem.has_key('src'):
                try:
                    self.split_content.append(('file', self.get_filename(elem['src']), elem))
                except UncompressableFileError:
                    if django_settings.DEBUG:
                        raise
            else:
                self.split_content.append(('hunk', elem.string, elem))
        
        return self.split_content