import os
import sys

sys.path.insert(0, os.path.abspath('../..'))
extensions = ['sphinx.ext.autodoc', ]


project = 'Hyperion'
copyright = '2018, Authors: see authors'
author = 'Authors: see authors'
version = '0.1'
release = '0.1'
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'
html_logo = 'img/logo_nanocd.png'
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': True,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}
html_static_path = ['_static']
