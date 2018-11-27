import datetime
import logging
import os

from google.appengine.ext import deferred
from google.appengine.ext import webapp

import config
import markup
import models
import post_deploy
import utils

from django import forms
import djangoforms

from django.forms import Widget
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.widgets import flatatt
from django.utils import simplejson

# from http://www.huyng.com/posts/django-custom-form-widget-for-dictionary-and-tuple-key-value-pairs/
# but modified, as the tuple thing totally doesn't work
class JsonPairInputs(Widget):
    """A widget that displays JSON Key Value Pairs
    as a list of text input box pairs

    Usage (in forms.py) :
    examplejsonfield = forms.CharField(label  = "Example JSON Key Value Field", required = False,
                                       widget = JsonPairInputs(val_attrs={'size':35},
                                                               key_attrs={'class':'large'}))

    """

    def __init__(self, *args, **kwargs):
        """A widget that displays JSON Key Value Pairs
        as a list of text input box pairs

        kwargs:
        key_attrs -- html attributes applied to the 1st input box pairs
        val_attrs -- html attributes applied to the 2nd input box pairs

        """
        self.key_attrs = {}
        self.val_attrs = {}
        if "key_attrs" in kwargs:
            self.key_attrs = kwargs.pop("key_attrs")
        if "val_attrs" in kwargs:
            self.val_attrs = kwargs.pop("val_attrs")
        Widget.__init__(self, *args, **kwargs)

    def render(self, name, value, attrs=None):
        """Renders this widget into an html string

        args:
        name  (str)  -- name of the field
        value (str)  -- a json string of a two-tuple list automatically passed in by django
        attrs (dict) -- automatically passed in by django (unused in this function)
        """

        if value is None or value.strip() is '': value = '{}'
        twotuple = simplejson.loads(force_unicode(value))

        ret = ''
        if value and len(value) > 0: 
            for i in twotuple:
                k = i.keys()[0]
                v = i[k]
                ctx = {'key':k,
                       'value':v,
                       'fieldname':name,
                       'key_attrs': flatatt(self.key_attrs),
                       'val_attrs': flatatt(self.val_attrs) }
                ret += '<input type="text" name="json_key[%(fieldname)s]" value="%(key)s" %(key_attrs)s> <input type="text" name="json_value[%(fieldname)s]" value="%(value)s" %(val_attrs)s><br />' % ctx
        return mark_safe(ret)

    def value_from_datadict(self, data, files, name):
        """
        Returns the simplejson representation of the key-value pairs
        sent in the POST parameters

        args:
        data  (dict)  -- request.POST or request.GET parameters
        files (list)  -- request.FILES
        name  (str)   -- the name of the field associated with this widget

        """
        if data.has_key('json_key[%s]' % name) and data.has_key('json_value[%s]' % name): 
            keys     = data.dict_of_lists()["json_key[%s]" % name] 
            values   = data.dict_of_lists()["json_value[%s]" % name]
            twotuple = []
            for key, value in zip(keys, values): 
                if len(key) > 0:
                    twotuple.append({key: value}) 
            jsontext = simplejson.dumps(twotuple) 
            return jsontext
        else:
            return None

# '[{"a":"b"},{"c":"d"}]'

class PostForm(djangoforms.ModelForm):
  title = forms.CharField(widget=forms.TextInput(attrs={'id':'name'}))
  body = forms.CharField(widget=forms.Textarea(attrs={
      'id':'message',
      'rows': 10,
      'cols': 20}))
  body_markup = forms.ChoiceField(
    choices=[(k, v[0]) for k, v in markup.MARKUP_MAP.iteritems()])
  tags = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 20}), required=False)
  recipients = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 20}), required=False)
  cc = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 20}), required=False)
  bcc = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 20}), required=False)
  draft = forms.BooleanField(required=False)
  headers = forms.CharField(label  = "Additional Headers", required = False, initial = '[{"placeholder":""},{"placeholder":""}]',
                                   widget = JsonPairInputs(val_attrs={'size':35},
                                                           key_attrs={'class':'large'}))
  class Meta:
    model = models.BlogPost
    fields = ['author', 'title', 'body', 'tags', 'recipients', 'cc', 'bcc', 'date_sent', 'headers' ]


def with_post(fun):
  def decorate(self, post_id=None):
    post = None
    if post_id:
      post = models.BlogPost.get_by_id(int(post_id))
      if not post:
        self.error(404)
        return
    fun(self, post)
  return decorate


class BaseHandler(webapp.RequestHandler):
  def render_to_response(self, template_name, template_vals=None, theme=None):
    if not template_vals:
      template_vals = {}
    template_vals.update({
        'path': self.request.path,
        'handler_class': self.__class__.__name__,
    })
    template_name = os.path.join("admin", template_name)
    self.response.out.write(utils.render_template(template_name, template_vals,
                                                  theme))


class AdminHandler(BaseHandler):
  def get(self):
    offset = int(self.request.get('start', 0))
    count = int(self.request.get('count', 20))
    posts = models.BlogPost.all().order('-published').fetch(count, offset)
    template_vals = {
        'offset': offset,
        'count': count,
        'last_post': offset + len(posts) - 1,
        'prev_offset': max(0, offset - count),
        'next_offset': offset + count,
        'posts': posts,
    }
    self.render_to_response("index.html", template_vals)


class PostHandler(BaseHandler):
  def render_form(self, form):
    self.render_to_response("edit.html", {'form': form})

  @with_post
  def get(self, post):
    self.render_form(PostForm(
        instance=post,
        initial={
          'draft': post and not post.path,
          'body_markup': post and post.body_markup or config.default_markup,
        }))

  @with_post
  def post(self, post):
    form = PostForm(data=self.request.POST, instance=post,
                    initial={'draft': post and post.published is None})
    if form.is_valid():
      post = form.save(commit=False)
      if form.cleaned_data['draft']:# Draft post
        post.published = datetime.datetime.max
        post.put()
      else:
        if not post.path: # Publish post
          post.updated = post.published = datetime.datetime.now()
        else:# Edit post
          post.updated = datetime.datetime.now()
        post.publish()
      self.render_to_response("published.html", {
          'post': post,
          'draft': form.cleaned_data['draft']})
    else:
      self.render_form(form)

class DeleteHandler(BaseHandler):
  @with_post
  def post(self, post):
    if post.path:# Published post
      post.remove()
    else:# Draft
      post.delete()
    self.render_to_response("deleted.html", None)


class PreviewHandler(BaseHandler):
  @with_post
  def get(self, post):
    # Temporary set a published date iff it's still
    # datetime.max. Django's date filter has a problem with
    # datetime.max and a "real" date looks better.
    if post.published == datetime.datetime.max:
      post.published = datetime.datetime.now()
    self.response.out.write(utils.render_template('post.html',
                                                  {'post': post}))

class RegenerateHandler(BaseHandler):
  def post(self):
    regen = post_deploy.PostRegenerator()
    deferred.defer(regen.regenerate)
    deferred.defer(post_deploy.post_deploy, post_deploy.BLOGGART_VERSION)
    self.render_to_response("regenerating.html")