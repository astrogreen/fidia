from django.db import models
from datetime import datetime
from vote.models import VoteModel
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils.html import escape, format_html


class Feature(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    title = models.CharField(max_length=140, blank=False, default="Title")
    description = models.TextField(blank=False, max_length=1000, default="Long description goes here")
    is_approved = models.BooleanField(default=False)
    user = models.ForeignKey(User, related_name='feature_user', default=1)

    def __str__(self):
        return '%s' % self.title


class Vote(VoteModel, models.Model):
    feature = models.ForeignKey(Feature, related_name='feature_votes', blank=False)
    user = models.ForeignKey(User, related_name='user_votes')


# catch each Feature's post_save signal and if successfully created, email the team for approval
@receiver(post_save, sender=Feature)
def create_new_sql_query(sender, instance=None, created=False, **kwargs):
    if created:
        # TODO add jira email issue create here
        print('EMAIL ASVO')
        print(instance.user)
        print(instance.title)

        # def send(self):
        #     user = str(instance.user)
        #     title = str(instance.title)
        #     description = str(instance.description)
        #     created = str(instance.created)
        #
        #     snippet = """
        #     <h4>ADC New Feature Request</h4>
        #         <table>
        #             <tr>
        #                 <td>User</td>
        #                 <td>{user}</td>
        #             </tr>
        #             <tr>
        #                 <td>Date</td>
        #                 <td>{created}</td>
        #             </tr>
        #             <tr>
        #                 <td>Title</td>
        #                 <td>{title}</td>
        #             </tr>
        #             <tr>
        #                 <td>Description</td>
        #                 <td>{description}</td>
        #             </tr>
        #         </table>
        #     """
        #
        #     subject, from_email, to = 'ADC New Feature Request', from_email, 'asvo-feedback@aao.gov.au'
        #
        #     html_content = format_html(snippet, user=user, from_email=from_email, description=description, created=created)
        #
        #     text_content = 'FROM: ' + user + ', ' + from_email + ' DESCRIPTION: ' + description + ' DATE: ' + created
        #     msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        #     msg.attach_alternative(html_content, "text/html")
        #     # msg.send(fail_silently=False)
