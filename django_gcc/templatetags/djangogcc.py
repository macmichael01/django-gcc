import time

from django import template
from django.core.cache import cache

try:
    from django.contrib.sites.models import Site
    DOMAIN = Site.objects.get_current().domain
except:
    DOMAIN = ''
    
from django_gcc import JsCompressor
from django_gcc.conf import settings

register = template.Library()


class DjangoGccNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        content = self.nodelist.render(context)
        
        if 'MEDIA_URL' in context:
            media_url = context['MEDIA_URL']
        else:
            media_url = settings.MEDIA_URL
        
        compressor = JsCompressor(content, media_url=media_url)
        
        in_cache = cache.get(compressor.cachekey)
        
        if in_cache:
            return in_cache
        else:
            # do this to prevent dog piling
            in_progress_key = '%s.django_gcc.in_progress.%s' % (DOMAIN, compressor.cachekey)
            added_to_cache = cache.add(in_progress_key, True, 300)
            
            if added_to_cache:
                output = compressor.output()
                # rebuilds the cache every 30 days if nothing has changed.
                cache.set(compressor.cachekey, output, 2591000)
                cache.set(in_progress_key, False, 300)
            else:
                while cache.get(in_progress_key):
                    time.sleep(0.1)
                output = cache.get(compressor.cachekey)
            return output


@register.tag
def djangogcc(parser, token):
    """
    Compresses linked and inline javascript into a single cached file.

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

    Which would be rendered something like::

        <script type="text/javascript" src="/media/CACHE/js/3f33b9146e12.js"></script>

    Linked files must be on your COMPRESS_URL (which defaults to MEDIA_URL).
    If DEBUG is true off-site files will throw exceptions. If DEBUG is false
    they will be silently stripped.
    
    """
    nodelist = parser.parse(('enddjangogcc',))
    parser.delete_first_token()

    args = token.split_contents()    
    return DjangoGccNode(nodelist)