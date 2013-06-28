from lib import aetycoon
import hashlib
import re
from google.appengine.ext import db
from google.appengine.ext import deferred
from google.appengine.api import urlfetch

import config
import generators
import markup
import static
import utils

import BeautifulSoup
import logging

if config.default_markup in markup.MARKUP_MAP:
  DEFAULT_MARKUP = config.default_markup
else:
  DEFAULT_MARKUP = 'html'


class BlogPost(db.Model):
  # The URL path to the blog post. Posts have a path iff they are published.
  path = db.StringProperty()
  title = db.StringProperty(required=True, indexed=False)
  body_markup = db.StringProperty(choices=set(markup.MARKUP_MAP),
                                  default=DEFAULT_MARKUP)
  body = db.TextProperty(required=True)
  tags = aetycoon.SetProperty(basestring, indexed=False)
  published = db.DateTimeProperty()
  updated = db.DateTimeProperty(auto_now=False)
  deps = aetycoon.PickleProperty()
  
  author = db.StringProperty()
  recipients = db.StringListProperty()
  cc = db.StringListProperty()
  bcc = db.StringListProperty()
  date_sent = db.DateTimeProperty()

  @aetycoon.TransformProperty(tags)
  def normalized_tags(tags):
    return list(set(utils.slugify(x.lower()) for x in tags))

  @property
  def tag_pairs(self):
    return [(x, utils.slugify(x.lower())) for x in self.tags]

  @property
  def rendered(self):
    """Returns the rendered body."""
    return markup.render_body(self)

  @property
  def summary(self):
    """Returns a summary of the blog post."""
    return markup.render_summary(self)

  @property
  def hash(self):
    val = (self.title, self.body, self.published)
    return hashlib.sha1(str(val)).hexdigest()

  @property
  def summary_hash(self):
    val = (self.title, self.summary, self.tags, self.published)
    return hashlib.sha1(str(val)).hexdigest()
  
  def publish(self):
    regenerate = False
    if not self.path:
      num = 0
      content = None
      while not content:
        path = utils.format_post_path(self, num)
        content = static.add(path, '', config.html_mime_type)
        num += 1
      self.path = path
      self.put()
      # Force regenerate on new publish. Also helps with generation of
      # chronologically previous and next page.
      regenerate = True 
      
      deferred.defer(self.mention)  # after publishing for the first time, try to ping sites you mention
    if not self.deps:
      self.deps = {}
    for generator_class, deps in self.get_deps(regenerate=regenerate):
      for dep in deps:
        if generator_class.can_defer:
          deferred.defer(generator_class.generate_resource, None, dep)
        else:
          generator_class.generate_resource(self, dep)
    self.put()
  
  def mention(self):
    if not self.path:
      return
    else:
      full_path = 'http://%s%s' % (config.host, self.path)
    if self.body_markup != 'html':
      return  # currently only works if the writing is done in HTML, I believe, a needless limitation
    
    soup = BeautifulSoup.BeautifulSoup(self.body)
    any_match = re.compile('.*')
    anchors = soup.findAll('a', attrs={'href':any_match})
    for a in anchors:
      href = a.get('href')
      # TODO: make sure it's an absolutely addressable href
      logging.info('Beginning process to mention href: %s' % href)
      response = urlfetch.fetch(href, method=urlfetch.GET)
      if response.status_code == 200:
        r_soup = BeautifulSoup.BeautifulSoup(response.content)
        endpoints = r_soup.findAll('link', attrs={'rel':'http://webmention.org/'})
        if len(endpoints) > 0:
          endpoint = endpoints[0].get('href')
          logging.info('Found endpoint %s and initiating a mention' % endpoint)
          mention_response = urlfetch.fetch(endpoint, method=urlfetch.POST, payload={'source':full_path, 'target':href})
          if mention_response.status_code == 202:
            # WebMention was received successfully!
            logging.info('Mention was accepted.')
            logging.info(mention_response.content)
          else:
            logging.error(mention_response.content)

  def remove(self):
    if not self.is_saved():   
      return
    if not self.deps:
      self.deps = {}
    # It is important that the get_deps() return the post dependency
    # before the list dependencies as the BlogPost entity gets deleted
    # while calling PostContentGenerator.
    for generator_class, deps in self.get_deps(regenerate=True):
      for dep in deps:
        if generator_class.can_defer:
          deferred.defer(generator_class.generate_resource, None, dep)
        else:
          if generator_class.name() == 'PostContentGenerator':
            generator_class.generate_resource(self, dep, action='delete')
            self.delete()
          else:
            generator_class.generate_resource(self, dep)  
  
  def get_deps(self, regenerate=False):
    for generator_class in generators.generator_list:
      new_deps = set(generator_class.get_resource_list(self))
      new_etag = generator_class.get_etag(self)
      old_deps, old_etag = self.deps.get(generator_class.name(), (set(), None))
      if new_etag != old_etag or regenerate:
        # If the etag has changed, regenerate everything
        to_regenerate = new_deps | old_deps
      else:
        # Otherwise just regenerate the changes
        to_regenerate = new_deps ^ old_deps
      self.deps[generator_class.name()] = (new_deps, new_etag)
      yield generator_class, to_regenerate


class VersionInfo(db.Model):
  bloggart_major = db.IntegerProperty(required=True)
  bloggart_minor = db.IntegerProperty(required=True)
  bloggart_rev = db.IntegerProperty(required=True)

  @property
  def bloggart_version(self):
    return (self.bloggart_major, self.bloggart_minor, self.bloggart_rev)
