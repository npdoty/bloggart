import secrets

# Name of the blog
blog_name = 'Bcc'

# Your name (used for copyright info)
author_name = 'Nick Doty'

# (Optional) slogan
slogan = 'An email blog from <a href="https://npdoty.name" rel="me">Nick Doty</a>.'

# The hostname this site will primarially serve off (used for Atom feeds)
host = 'bcc.npdoty.name'

# Selects the theme to use. Theme names correspond to directories under
# the 'themes' directory, containing templates and static content.
theme = 'bcc'

# Defines the URL organization to use for blog postings. Valid substitutions:
#   slug - the identifier for the post, derived from the title
#   year - the year the post was published in
#   month - the month the post was published in
#   day - the day the post was published in
post_path_format = '/%(slug)s'

# A nested list of sidebar menus, for convenience. If this isn't versatile
# enough, you can edit themes/default/base.html instead.
sidebars = [
  # ('Blogroll', [
  #   ('Nick Johnson', 'http://blog.notdot.net/'),
  #   ('Bill Katz', 'http://www.billkatz.com/'),
  #   ('Coding Horror', 'http://www.codinghorror.com/blog/'),
  #   ('Craphound', 'http://craphound.com/'),
  #   ('Neopythonic', 'http://www.neopythonic.blogspot.com/'),
  #   ('Schneier on Security', 'http://www.schneier.com/blog/'),
  # ]),
]

# Number of entries per page in indexes.
posts_per_page = 5

# The mime type to serve HTML files as.
html_mime_type = "text/html; charset=utf-8"

# To use disqus for comments, set this to the 'short name' of the disqus forum
# created for the purpose.
disqus_forum = None

# Length (in words) of summaries, by default
summary_length = 200

# If you want to use Google Analytics, enter your 'web property id' here
analytics_id = 'UA-7375818-1'

# If you want to use PubSubHubbub, supply the hub URL to use here.
# hubbub_hub_url = 'http://pubsubhubbub.appspot.com/'
hubbub_hub_url = None


# If you want to ping Google Sitemap when your sitemap is generated change this to True, else False
# see: http://www.google.com/support/webmasters/bin/answer.py?hl=en&answer=34609 for more information
google_sitemap_ping = False

# If you want to use Google Site verification, go to 
# https://www.google.com/webmasters/tools/ , add your site, choose the 'upload
# an html file' method, then set the NAME of the file below.
# Note that you do not need to download the file provided - just enter its name
# here.
google_site_verification = None

# Default markup language for entry bodies (defaults to html).
default_markup = 'html'

# Syntax highlighting style for RestructuredText and Markdown,
# one of 'manni', 'perldoc', 'borland', 'colorful', 'default', 'murphy',
# 'vs', 'trac', 'tango', 'fruity', 'autumn', 'bw', 'emacs', 'pastie',
# 'friendly', 'native'.
highlighting_style = 'friendly'

# Absolute url of the blog application use '/blog' for host/blog/ 
# and '' for host/.Also remember to change app.yaml accordingly 
url_prefix = ''

# Defines where the user is defined in the rel="me" of your pages.
# This allows you to expand on your social graph.
rel_me = 'https://npdoty.name'