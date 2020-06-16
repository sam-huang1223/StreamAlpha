"""
send daily trade activity to interested subscribers (e.g. mom)
    also maybe include performance on trades from last week/month/3 months/year

Use https://sendgrid.com/marketing/sendgrid-services-cro/#pricing-app
    (https://realpython.com/python-send-email/#transactional-email-services)
"""

import os
import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail

sg = sendgrid.SendGridAPIClient(
    apikey=os.environ.get("SENDGRID_API_KEY")
)
from_email = Email("my@gmail.com")
to_email = Email("your@gmail.com")
subject = "A test email from Sendgrid"
content = Content(
    "text/plain", "Here's a test email sent through Python"
)
mail = Mail(from_email, subject, to_email, content)
response = sg.client.mail.send.post(request_body=mail.get())

# The statements below can be included for debugging purposes
print(response.status_code)
print(response.body)
print(response.headers)