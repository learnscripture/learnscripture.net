=============
 Android app
=============

There used to be a LearnScripture.net app on Google Play Store. It has now been
pulled.

The app simply loaded http://learnscripture.net in a WebView, and had a few
tweaks to integrate the menu button, back button etc., and a custom menu. The
website also had a few tweaks to make it work better with the Android app,
including the ability to call a few Java functions that are exposed via the
``window.androidlearnscripture`` object.

In practice, the Android app was a pain:

* It appears that Google Play Store gives you no way of being notified of new
  comments about the app. When people report problems, you are not notified, and
  have no way of getting more info anyway.

* The many different versions of Android, all with outdated WebView components,
  made compatibility a nightmare.

* Every time a change was needed to the app, getting the app to build again was
  a pain - the Android Studio tools update themselves, and break or require
  changes.

Now, the app no longer works and has been pulled from the app store.

The source code for the app is here:

https://bitbucket.org/spookylukey/net.learnscripture.webviewapp

Integration with the app was removed in 172ca0b13c72 and 712939385c29.
