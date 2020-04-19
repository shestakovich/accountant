from django import template

register = template.Library()


@register.filter
def extract_duration(duration):
    if duration is None:
        return None
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds // 60) % 60
    if not hours:
        return format_minutes((total_seconds // 60) % 60)
    if not minutes:
        return format_hours(hours)
    return f"{format_hours(hours)} {format_minutes(minutes)}"


def format_hours(hours):
    if hours % 10 == 1 and hours % 100 != 11:
        return f"{hours} час"
    elif 2 <= hours % 10 <= 4 and not 12 <= hours % 100 <= 14:
        return f"{hours} часа"
    return f"{hours} часов"


def format_minutes(minutes):
    if minutes % 10 == 1 and minutes % 100 != 11:
        return f"{minutes} минута"
    elif 2 <= minutes % 10 <= 4 and not 12 <= minutes % 100 <= 14:
        return f"{minutes} минуты"
    return f"{minutes} минут"
