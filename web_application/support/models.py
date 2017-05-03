from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from time import gmtime, strftime
from django.utils.html import escape, format_html
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives


class Contact(models.Model):
    name = models.CharField(max_length=100, blank=False)
    email = models.EmailField(max_length=100, blank=False)
    message = models.CharField(max_length=100, blank=False)


class BugReport(models.Model):
    name = models.CharField(max_length=100, blank=False)
    email = models.EmailField(max_length=100, blank=False)
    message = models.CharField(max_length=10000, blank=False)
    url = models.CharField(max_length=100, blank=True)
    SURVEY_TEAM = (
        ('NA', 'Not applicable'),
        ('GAMA', 'GAMA'),
        ('SAMI', 'SAMI'),
        ('GALAH', 'GALAH'),
    )
    survey_team = models.CharField(choices=SURVEY_TEAM, default='NA', max_length=100)


@receiver(pre_save, sender=Contact)
def email_contact_form(sender, instance, **kwargs):
    from_email = str(instance.email)
    message = str(instance.message)
    name = str(instance.name)
    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    snippet = """
    <h4>ADC Contact Form Message</h4>
        <table>
            <tr>
                <td>Name</td>
                <td>{name}</td>
            </tr>
            <tr>
                <td>Email</td>
                <td>{from_email}</td>
            </tr>
            <tr>
                <td>Date</td>
                <td>{date}</td>
            </tr>
            <tr>
                <td>Message</td>
                <td>{message}</td>
            </tr>
        </table>
    """

    subject, from_email, to = 'ADC Contact Form', from_email, 'asvo-feedback@aao.gov.au'
    html_content = format_html(snippet, name=name, from_email=from_email, message=message, date=date)
    text_content = 'FROM: ' + name + ', ' + from_email + ' MESSAGE: ' + message + ' DATE: ' + date
    print('email sent')
    send_email(subject=subject, html_content=html_content, text_content=text_content, from_email=from_email, to=to)


@receiver(pre_save, sender=BugReport)
def email_bug_report(sender, instance, **kwargs):
    from_email = str(instance.email)
    survey_team = str(instance.survey_team)
    message = str(instance.message)
    url = str(instance.url)
    name = str(instance.name)
    date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    snippet = """
    <h4>ADC Bug Report</h4>
        <table>
            <tr>
                <td>External Reporter</td>
                <td>{name}</td>
            </tr>
            <tr>
                <td>Email</td>
                <td>{from_email}</td>
            </tr>
            <tr>
                <td>Survey Team</td>
                <td>{survey_team}</td>
            </tr>
            <tr>
                <td>Date</td>
                <td>{date}</td>
            </tr>
            <tr>
                <td>URL</td>
                <td>{url}</td>
            </tr>
            <tr>
                <td>Message</td>
                <td>{message}</td>
            </tr>
        </table>
    """

    subject, from_email, to = 'ADC Bug Report', from_email, 'adc-bugs@aao.gov.au'
    html_content = format_html(snippet, name=name, from_email=from_email, url=url, message=message, date=date, survey_team=survey_team)
    text_content = 'FROM: ' + name + ', ' + from_email + ', URL:' + url + ' MESSAGE: ' + message + ' DATE: ' + date

    send_email(subject=subject, html_content=html_content, text_content=text_content, from_email=from_email, to=to)


def send_email(subject, html_content, text_content, from_email, to):
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
