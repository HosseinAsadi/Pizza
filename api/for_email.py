import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(mess, receiver, title=None):
    mail_content = mess
    sender_gmail = 'pizza.amicos.clifton@gmail.com'
    sender_pass = 'Cisco1991'
    message = MIMEMultipart()
    message['From'] = sender_gmail
    message['To'] = receiver
    message['Subject'] = 'Pizza App' if title is None else title
    message.attach(MIMEText(mail_content, 'plain'))
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    session.login(sender_gmail, sender_pass)
    text = message.as_string()
    session.sendmail(sender_gmail, receiver, text)
    session.quit()
