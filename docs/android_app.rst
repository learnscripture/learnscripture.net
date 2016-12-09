=============
 Android app
=============

There used to be a LearnScripture.net app on Google Play Store. It has now been pulled,
but some people may still be using it (despite a message telling them it is unsupported).

The source code for the app is here:

https://bitbucket.org/spookylukey/net.learnscripture.webviewapp

The app simply loads http://learnscripture.net in a WebView, and has a few
tweaks to integrate the menu button, back button etc., and a custom menu. The
website also has a few tweaks to make it work better with the Android app,
including the ability to call a few Java functions that are exposed via the
``window.androidlearnscripture`` object.

In practice, the Android app was a pain:

* It appears that Google Play Store gives you no way of being notified of new
  comments about the app. When people report problems, you are not notified, and
  have no way of getting more info anyway.

* The many different versions of Android, all with outdated WebView components,
  made compatibility a nightmare.

* Every time a change is needed to the app, getting the app to build again was
  a pain - the Android Studio tools update themselves, and break or require
  changes.

It is generally better to get users to access the site via Firefox/Chrome on
their mobile device. For this reason, the app has been retired. A message is
selectively displayed to app users (by checking for
``window.androidlearnscripture`` from Javascript) and telling them to use
a normal web browser. In the future, all support for this app should be removed.
