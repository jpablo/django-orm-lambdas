# LambdaManager

LambdaManager extends the regular django.db.models.Manager with one function:

<pre>
where(lambda x: ...)
</pre>

that can be used like this:

## Example

<pre>
# in models.py:

from django.db import models
from lambda_manager import LambdaManager

class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    objects = LambdaManager()

class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    choice = models.CharField(max_length=200)
    votes = models.IntegerField()
    anumber = models.IntegerField()

    objects = LambdaManager()
</pre>


<pre>
# elsewhere:

from models import Choice

Choice.objects.where(lambda c: c.votes >= 1)
Choice.objects.where(lambda c: c.votes != 1)
Choice.objects.where(lambda c: c.poll.question.exact('aaa'))
Choice.objects.where(lambda c: c.poll.question.contains('aa'))
Choice.objects.where(lambda c: c.votes == c.anumber)
Choice.objects.where(lambda c: c.votes > c.anumber)
Choice.objects.where(lambda x: x.votes < x.votes + 1)
Choice.objects.where(lambda x: x.votes < x.votes + x.votes + 2)

</pre>

TODO: Implement other arithmetic operators: *, -, /

Entry.objects.filter(n_comments__gt=F('n_pingbacks') * 2)

