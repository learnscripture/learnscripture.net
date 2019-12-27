# Path to repo or hgweb config to serve (see 'hg help hgweb')
config = "/home/%(proj_user)s/repos/hgweb.config".encode("ascii")

# demandloading reduces startup time,
# but gives us a strange import error
# from mercurial import demandimport; demandimport.enable()

from mercurial.hgweb import hgweb
application = hgweb(config)
