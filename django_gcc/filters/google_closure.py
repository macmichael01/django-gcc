import httplib
import mimetypes
import os
import re
import subprocess
import urllib

from django.conf import settings

from django_gcc.filters import FilterBase, FilterError
from django_gcc.utils import get_file_hash

URL_PATTERN = re.compile(r'url\(([^\)]+)\)')

GCC_API_ENABLED = getattr(settings, 'COMPRESS_GCC_API_ENABLED', False)
GCC_BINARY = getattr(settings, 'COMPRESS_GCC_BINARY', 'java -jar compiler.jar')
GCC_SERVER = httplib.HTTPConnection('closure-compiler.appspot.com')
GCC_ARGUMENTS = getattr(settings, 'COMPRESS_GCC_ARGUMENTS', {})
GCC_COMPILATION_LEVEL = GCC_ARGUMENTS.get('compilation_level', 'ADVANCED_OPTIMIZATIONS')


class GoogleClosureCompilerFilter(FilterBase):
    
    def __init__(self, content, gcc_api_enabled=GCC_API_ENABLED, gcc_server=GCC_SERVER,
                 gcc_binary=GCC_BINARY, gcc_arguments=GCC_ARGUMENTS,
                 gcc_compilation_level=GCC_COMPILATION_LEVEL, *args, **kwargs):
        
        self.gcc_api_enabled = gcc_api_enabled
        self.connection = gcc_server
        self.gcc_binary = gcc_binary
        self.gcc_arguments = gcc_arguments
        self.gcc_compilation_level = gcc_compilation_level
        super(GoogleClosureCompilerFilter, self).__init__(content, *args, **kwargs)
    
    
    def input(self, filename=None, media_url=None, **kwargs):
        media_url = media_url or settings.MEDIA_URL
        media_root = os.path.abspath(settings.MEDIA_ROOT)
        
        if filename is not None:
            filename = os.path.abspath(filename)
            
        if not filename or not filename.startswith(media_root):
            return self.content
            
        self.media_path = filename[len(media_root):]
        self.media_path = self.media_path.lstrip('/')
        self.media_url = media_url.rstrip('/')
        self.mtime = get_file_hash(filename)
        self.has_http = False
        
        if self.media_url.startswith('http://') or self.media_url.startswith('https://'):
            self.has_http = True
            parts = self.media_url.split('/')
            self.media_url = '/'.join(parts[2:])
            self.protocol = '%s/' % '/'.join(parts[:2])
        
        self.directory_name = '/'.join([self.media_url, os.path.dirname(self.media_path)])
        output = URL_PATTERN.sub(self.url_converter, self.content)
        
        return output
        
    def url_converter(self, matchobj):
        url = matchobj.group(1)
        url = url.strip(' \'"')
        
        if (url.startswith('http://') or
            url.startswith('https://') or
            url.startswith('/') or
            url.startswith('data:')):
            return "url('%s')" % self.add_mtime(url)
        
        full_url = '/'.join([str(self.directory_name), url])
        full_url = posixpath.normpath(full_url)
        
        if self.has_http:
            full_url = "%s%s" % (self.protocol, full_url)
        
        return "url('%s')" % self.add_mtime(full_url)
        
    def filter_common(self, content, arguments):    
        if self.gcc_api_enabled:      
            headers = {"Content-type": "application/x-www-form-urlencoded"}
            params = urllib.urlencode([
                ('js_code', content),
                ('compilation_level', self.gcc_compilation_level),
                ('output_format', 'text'),
                ('output_info', 'compiled_code'),
              ])
            self.connection.request('POST', '/compile', params, headers)
            response = self.connection.getresponse()
            
            if response.status != 200:
                err = 'Unable to apply Google Closure Compiler filter'
                raise FilterError(err)
            
            if self.verbose:
                print err
                
            filtered_js = response.read()
            self.connection.close()
        else:                
            command = self.gcc_binary
            for argument in arguments:
                command += ' --' + argument + ' ' + arguments[argument]
        
            if self.verbose:
                command += ' --verbose'
            print self.gcc_compilation_level
            command += ' --compilation_level %s' % self.gcc_compilation_level
            
            p = subprocess.Popen(command, 
                shell=True, 
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            p.stdin.write(content)            
            filtered_js, err = p.communicate()
            
            if p.wait() != 0:
                if not err:
                    err = 'Unable to apply Google Closure Compiler filter'
                
                raise FilterError(err)
            
            if self.verbose:
                print err
            
            p.stdin.close()
            
        return filtered_js
            
    def output(self, js):
        return self.filter_common(js, self.gcc_arguments)