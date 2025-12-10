import math

def ramp(x,y,t,*etc):
    
    coef = 1.0
    if (t < 100.0):
        coef = math.floor(t) / 100.0

    return coef # originally in Stephs ismip was return -coef
