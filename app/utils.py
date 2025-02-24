from django.utils.timezone import now

def time_since(timestamp):
    if not timestamp:
        return "Unknown"

    diff = now() - timestamp

    seconds = diff.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    weeks = days // 7
    months = days // 30
    years = days // 365

    if seconds < 10:
        return "A few seconds ago"
    elif seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif minutes < 2:
        return "1 min ago"
    elif minutes < 60:
        return f"{int(minutes)} mins ago"
    elif hours < 2:
        return "1 hour ago"
    elif hours < 24:
        return f"{int(hours)} hours ago"
    elif days < 2:
        return "1 day ago"
    elif days < 7:
        return f"{int(days)} days ago"
    elif weeks < 2:
        return "1 week ago"
    elif weeks < 4:
        return f"{int(weeks)} weeks ago"
    elif months < 2:
        return "1 month ago"
    elif months < 12:
        return f"{int(months)} months ago"
    elif years < 2:
        return "1 year ago"
    else:
        return f"{int(years)} years ago"
