import pandas as pd
import numpy as np

def time_convert(x):
    parts = x.split(":")
    
    if len(parts) == 3:           # hh:mm:ss
        h,m,s = map(float,x.split(':'))
        return (h*60+m)*60+s
    
    elif len(parts) == 2:         # mm:ss
        m, s = map(float, x.split(':'))
        return m*60 + s
    else:
        return

def pace_to_float(p):
    mins, secs = p.split(":")
    return int(mins) + int(secs)/60

def get_time_of_day(dt):
    """Devuelve mañana / tarde / noche según la hora."""
    h = dt.hour
    if 6 <= h < 12:
        return "mañana"
    elif 12 <= h < 18:
        return "tarde"
    else:
        return "noche"