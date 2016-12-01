=============
 Android app
=============

There is currently a LearnScripture.net app on Google Play Store:

https://play.google.com/store/apps/details?id=net.learnscripture.webviewapp

The source code for the app is here:

https://bitbucket.org/spookylukey/net.learnscripture.webviewapp

The app simply loads http://learnscripture.net in a WebView, and has a few
tweaks to integrate the menu button, back button etc., and a custom menu. The
website also has a few tweaks to make it work better with the Android app,
including the ability to call a few Java functions that are exposed via the
``window.androidlearnscripture`` object.

In practice, the Android app is a pain:

* it appears that Google Play Store gives you no way of being notified of new
  comments about the app. When people report problems, you are not notified, and
  have no way of getting more info anyway.

* The many different versions of Android, all with outdated WebView components,
  makes compatibility a nightmare.

* Every time a change is needed to the app, getting the app to build again is
  a pain - the Android Studio tools update themselves, and break or require
  changes.

It is generally better to get users to access the site via Firefox/Chrome on
their mobile device. For this reason, the app should be retired. A message could
be displayed selectively to app users by checking for
``window.androidlearnscripture`` from Javascript.
