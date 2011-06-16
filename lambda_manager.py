__author__ = 'jpablo'

from functools import partial


class Expression(object):
    mapping = {}

    def __init__(self, expr):
        self.expr = expr

    def head(self):
        return self.expr[0]

    def args(self):
        return self.expr[1:]

    def __repr__(self):
        return str([self.head()] + self.args())

    def __neg__(self):
        return Expression(['-', self])

    def __add__(self, other):
        return Expression(['+', self, other])

    def __radd__(self, other):
        return Expression(['+', self, other])

    def __sub__(self, other):
        return Expression(['-', self, other])

    def __rsub__(self, other):
        return Expression(['-', other, self])

    def __mul__(self, other):
        return Expression(['*', self, other])

    def __rmul__(self, other):
        return Expression(['*', self, other])

    def __div__(self, other):
        return Expression(['/', self, other])

    def __rdiv__(self, other):
        return Expression(['/', other, self])

    def __pow__(self, other):
        return Expression(['^', self, other])

    def __xor__(self, other):
        return Expression(['^', self, other])

    def __eq__(self, other):
        return Expression(['==', self, other])

    def __ne__(self, other):
        return Expression(['!=', self, other])

    def __lt__(self, other):
        return Expression(['<', self, other])

    def __le__(self, other):
        return Expression(['<=', self, other])

    def __gt__(self, other):
        return Expression(['>', self, other])

    def __ge__(self, other):
        return Expression(['>=', self, other])

    def  __call__(self, *others):
        return Expression(['call', self] + list(others))

    def __getattr__(self, item):
        return Expression(['getattr', self, item])

    @staticmethod
    def eval(ob):
        """
        builds keyword arguments for filter or exclude
        """
        if is_expression(ob):
            if ob.head() in ('var', 'getattr'):
                return var(flatten_attribute(ob))

            evaluated_args = map(Expression.eval, ob.args())

            return Expression.mapping[ob.head()](*evaluated_args)

        if is_primitive(ob) or callable(ob):
            return ob


def is_expression(ob):
    return isinstance(ob, Expression)

def is_primitive(ob):
    return type(ob) in (str, unicode, int, float)

def function(expression, arg):
    field = expression.args()[0]
    kwargs = {field: arg}
    return kwargs


def boolean_operator(opname, expr1, expr2):
    field = expr1.args()[0]
    kwargs = {}
    if opname == 'ne':
        opname = 'exact'
        kwargs['exclude'] = True
    op = field + '__' + opname

    kwargs[op] = expr2
    if is_expression(expr2):
        kwargs[op] = models.F(remove_fieldname(expr2))
    return kwargs

#def sum_operator(expr1, expr2):
#    field1 = expr1.args()[0]

def plus(expr1, expr2):
    if is_expression(expr1):
        if expr1.head() == 'var':
            left = models.F(remove_fieldname(expr1))
        else:
            left = Expression.eval(expr1)

    else:
        ## we assume is an ExpressionNode
        left = expr1

    if is_primitive(expr2):
        right = expr2
    elif is_expression(expr2):
        if expr2.head() == 'var':
            right = models.F(remove_fieldname(expr2))
        else:
            right = Expression.eval(expr2)
    return left + right

def remove_fieldname(expression):
    right_field = expression.args()[0]
    variable_name = right_field .split('__')[0]
    return right_field.replace(variable_name + '__', '', 1)


def _flatten_attribute(expression):
    if expression.head() == 'var':
        return [expression.args()[0]]
    elif expression.head() == 'getattr':
        left_expr, attribute = expression.args()
        return _flatten_attribute(left_expr) + [attribute]


def flatten_attribute(expression):
    return '__'.join(_flatten_attribute(expression))

Expression.mapping = {
    '<': partial(boolean_operator, 'lt'),
    '<=': partial(boolean_operator, 'lte'),
    '>': partial(boolean_operator, 'gt'),
    '>=': partial(boolean_operator, 'gte'),
    '==': partial(boolean_operator, 'exact'),
    '!=': partial(boolean_operator, 'ne'),
    'call': function,
    '+': plus
}

def func(callable):
    return Expression(['func', callable])


def var(name):
    return Expression(['var', name])



def create_proxy(model):
    fields = dict([(f.name, var(f.name)) for f in model._meta.fields])
    proxy = type('ModelProxy', (object,), fields)
    return proxy


#votes = var('votes')
#
#print Expression.eval(votes.aa > 1)


try:
    from django.db import models

    class LambdaManager(models.Manager):
        def where(self, func, show_querystr = False):
            proxy = create_proxy(self.model)
            kwargs = Expression.eval(func(proxy()))
            if show_querystr:
                return kwargs
            if kwargs.has_key('exclude'):
                del kwargs['exclude']
                return self.model.objects.exclude(**kwargs)
            else:
                return self.model.objects.filter(**kwargs)
except:
    pass

