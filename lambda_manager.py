__author__ = 'jpablo'

from functools import partial
from django.db import models

class Expression(object):

    mapping = {}
    class_name = 'Expression'

    def __init__(self, expr):
        self.expr = expr

    def head(self):
        return self.expr[0]

    def args(self):
        return self.expr[1:]

    def __repr__(self):
        return str([self.head()] + self.args())

    def __neg__(self):
        return Expression(['-',  self])

    def __add__(self, other):
        return Expression(['+',  self,  other])

    def __radd__(self, other):
        return Expression(['+',  self,  other])

    def __sub__(self, other):
        return Expression(['-',  self,  other])

    def __rsub__(self, other):
        return Expression(['-',  other,  self])

    def __mul__(self, other):
        return Expression(['*',  self,  other])

    def __rmul__(self, other):
        return Expression(['*',  self,  other])

    def __div__(self, other):
        return Expression(['/',  self,  other])

    def __rdiv__(self, other):
        return Expression(['/',  other, self])

    def __pow__(self, other):
        return Expression(['^',  self,  other])

    def __xor__(self, other):
        return Expression(['^',  self,  other])

    def __eq__(self, other):
        return Expression(['==',  self,  other])
    
    def __ne__(self, other):
        return Expression(['!=',  self,  other])

    def __lt__(self, other):
        return Expression(['<',  self,  other])

    def __le__(self, other):
        return Expression(['<=',  self,  other])

    def __gt__(self, other):
        return Expression(['>',  self,  other])

    def __ge__(self, other):
        return Expression(['>=',  self,  other])

    def  __call__(self, *others):
        return Expression(['call', self] +  list(others) )

    def __getattr__(self, item):
        return Expression(['getattr', self, item])

    @staticmethod
    def eval(ob):
        if is_expression(ob):
            if ob.head() == 'var':
                val = ob.expr[2]
                if val is not None:
                    return Expression.eval( val )
                else:
                    return ob
            if ob.head() == 'getattr':
                return var(flatten_attribute( ob ))

            evaluated_args = map(Expression.eval,ob.args())

            return Expression.mapping[ob.head()](*evaluated_args)

        if type(ob) in (str,unicode,int,float) or callable(ob):
            return ob


def is_expression(ob):
    return getattr(ob,'class_name','') == 'Expression'


def function(expression,arg):
    field = expression.args()[0]
    kwargs = {}
    kwargs[field] = arg
    return kwargs
    return kwargs

def boolean_operator(opname, expression, value):
    field = expression.args()[0]
    kwargs = {}
    if opname == 'ne':
        opname = 'exact'
        kwargs['exclude'] = True
    op = field + '__' + opname

    kwargs[op] = value
    if is_expression(value):
        kwargs[op] = models.F(remove_fieldname(value))
    return kwargs

#def sum_operator(expr1, expr2):
#    field1 = expr1.args()[0]


def remove_fieldname(expression):
    right_field = expression.args()[0]
    variable_name = right_field .split('__')[0]
    return right_field.replace(variable_name+'__','',1)

def _flatten_attribute(expression):
    if expression.head() == 'var':
        return [expression.args()[0]]
    elif expression.head() == 'getattr':
        left_expr, attribute = expression.args()
        return _flatten_attribute(left_expr) + [attribute]

def flatten_attribute(expression):
    return '__'.join(_flatten_attribute(expression))

django_mapping = {
    '<':  partial(boolean_operator,'lt'),
    '<=':  partial(boolean_operator,'lte'),
    '>':  partial(boolean_operator,'gt'),
    '>=':  partial(boolean_operator,'gte'),
    '==':  partial(boolean_operator,'exact'),
    '!=':  partial(boolean_operator,'ne'),
    'call': function
}

def func(callable):
    return Expression(['func', callable])

def var(name, val = None):
    return Expression(['var',name, val])

def set(var_expr, val):
    var_expr.expr[2] = val
    return val


def create_proxy(model):
    fields = dict([(f.name,var(f.name)) for f in model._meta.fields])
    proxy =  type('ModelProxy',(object,),fields)
    return proxy


Expression.mapping = django_mapping

#votes = var('votes')
#
#print Expression.eval(votes.aa > 1)


class LambdaManager(models.Manager):

    def where(self, func):
        proxy = create_proxy(self.model)
        kwargs = Expression.eval( func(proxy()) )
        if kwargs.has_key('exclude'):
            del kwargs['exclude']
            return self.model.objects.exclude(**kwargs)
        else:
            return self.model.objects.filter(**kwargs)


## Examples:

## in models.py:

#from django.db import models
#from lambda_manager import LambdaManager
#
#class Poll(models.Model):
#    question = models.CharField(max_length=200)
#    pub_date = models.DateTimeField('date published')

#    objects = LambdaManager()
#
#class Choice(models.Model):
#    poll = models.ForeignKey(Poll)
#    choice = models.CharField(max_length=200)
#    votes = models.IntegerField()
#
#    objects = LambdaManager()


#Choice.objects.where(lambda c: c.votes >= 1)
#Choice.objects.where(lambda c: c.votes != 1)
#Choice.objects.where(lambda c: c.poll.question.exact('aaa'))
#Choice.objects.where(lambda c: c.poll.question.contains('aa'))