========================
 Development principles
========================

The usual things for developing a Django app apply. Test driven development is
very helpful for many things - see `<project_structure.rst>`_ for more.

Additionally, more specifically to LearnScripture.net:

* For a large number of users mobile devices are their primary device. The site
  should have a first class experience on small screens and touch screens,
  and in low bandwidth situations. A lot of effort has been put into ensuring
  that pages load quickly, with very few HTTP resources being loaded, and
  aggressively cached where possible.

  Both aspects (limited bandwidth and screen space) mean that adverts
  of any kind would seriously hinder the experience.

* A significant number of users are children. We've aimed to make the interface
  simple enough for even quite young children to use.

* We've aimed to add motivational features that promote long-term Bible
  memorisation habits.
