import datetime

from django import template
from django.template import defaultfilters
from django.utils import timezone


register = template.Library()


@register.simple_tag
def render_label(bound_field, **kwargs):
    markup = bound_field.label_tag(attrs=kwargs)

    return markup


@register.simple_tag
def render_input(bound_field, **kwargs):
    # This logic is copied from BoundField.__str__.
    markup = bound_field.as_widget(attrs=kwargs)

    if bound_field.field.show_hidden_initial:
        markup = markup + bound_field.as_hidden(only_initial=True)

    return markup


def _since(dt, moment):
    """Returns the time since for a date, like '1 year' or '12 hours'."""
    one_day = 3600 * 24

    periods = [
        (one_day * 365, u'year', u'years'),
        (one_day * 28, u'month', u'months'),
        (one_day, u'day', u'days'),
        (3600, u'hour', 'hours'),
        (60, u'minute', u'minutes'),
        (1, u'second', u'seconds'),
    ]

    delta = moment - dt

    for period, singular, plural in periods:
        num = delta.seconds // period

        if num:
            form = singular if num == 1 else plural

            return u'%d %s' % (num, form)
    else:
        return u'0 seconds'


@register.filter
def since(dt, arg=None):
    moment = timezone.now()

    if (moment - dt) > datetime.timedelta(hours=23):
        return defaultfilters.date(dt, arg)

    else:
        return _since(dt, moment) + u' ago'


@register.simple_tag
def params(qdict, **kwargs):
    """Helper for building a query string, adding and removing params to
    an existing query dict.

    In a template, use it like:

    {% params request.GET page=4 %}
    """
    qdict = qdict.copy()

    for name, value in kwargs.items():
        if value is None:
            if name in qdict:
                del qdict[name]
        else:
            qdict[name] = value

    return qdict.urlencode()