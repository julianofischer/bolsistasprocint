import datetime

from django import template

register = template.Library()

@register.filter
def add_days(value, days):
    return value + datetime.timedelta(days=days)

@register.filter
def timedelta_hours(value):
    total_seconds = value.total_seconds()        
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours, minutes, seconds = int(hours), int(minutes), int(seconds)
    return f"{hours:02}:{minutes:02}:{seconds:02}"