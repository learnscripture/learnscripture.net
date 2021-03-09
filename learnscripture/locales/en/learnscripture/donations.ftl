### Donations.

# 'Product name' that appears in PayPal if user is making a donation
donations-paypal-title = Donation to LearnScripture.net

## Donate page.

# Page title
donations-page-title = Donate

donations-page-top-html =
  <p>LearnScripture.net is funded entirely by donations.
  If you would like to donate to support the ongoing costs of running this site, that would be much appreciated!</p>

  <p>Our running costs include:</p>
  <ul>
    <li>Web server hosting (currently about &pound;60/year)</li>
    <li>Domain name</li>
    <li>Other services we use to ensure good service.</li>
  </ul>

  <p>You can donate as much or as little as you like! If a significant fraction
  of users gave $5.00 or £5.00 every 3 years, that would go a long way!</p>

  <p><b>Due to an issue with our PayPal account, we are not currently accepting donations.</b></p>

# Message displayed on donations page if user is not logged in
donations-login-or-signup-to-donate-html = Please <a href="{ $login_and_redirect_url }">log in</a>
      (or <a href="{ $signup_and_redirect_url }">create an account</a>) to donate, so that we track your donation.



## Donation complete page.

# Page title
donations-completed-page-title = Donation complete

# Thank you message
donations-done-thank-you = Thank you for your donation!

## Donation cancelled page.

# Page title
donations-cancelled-page-title = Donation cancelled

donations-cancelled-message-html = You cancelled part way through the payment process. You can <a href="{ $donate_url }">return to the donation page</a>.

## Donation received email.

donations-donation-received-subject = LearnScripture.net - donation received

donations-donation-received-email =
    Hi { $account_name },

    Thank you for your donation of { $payment_amount }!

    Donations like these really help to keep the site running, and
    allow us to make further improvements to the service.

    We hope you continue to enjoy and benefit from your use of the site!

    The LearnScripture.net team.


## Target reached email.


# Email sent out to donators when the target is reached,
# $name is the user's username,
# $target is the target of the donation drive (a number in GBP),
# $amount is the amount the user gave (a number in GBP)
donations-target-reached-email = Hi { $name },

  Our target of { $target } was reached!

  Thanks to your contribution of { $amount } we reached our funding target.

  This money is used to pay for the ongoing costs of the LearnScripture.net
  service, including hosting costs and other services.

  Thanks so much for your support,

  The LearnScripture.net team.


# Subject of email sent out to donators when the target is reached
donations-target-reached-email-subject = LearnScripture.net - donation target reached!
