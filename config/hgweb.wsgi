# Path to repo or hgweb config to serve (see 'hg help hgweb')
config = "/home/%(proj_user)s/repos/hgweb.config"

# enable demandloading to reduce startup time
from mercurial import demandimport; demandimport.enable()

from mercurial.hgweb import hgweb
application = hgweb(config)
