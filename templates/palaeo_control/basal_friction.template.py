import math

def bedFricCalc(topg, thck, cmin, cmax, z0):

    zbase = topg
    cmin = 7000. # based on modern inverted
    cmax = @WeertC 
    z0 = -2000. # based on best performing from mini ensemble
    
    if thck == 0:
        frictionCoef=100
        
    elif thck != 0:
        if topg < 0:
            foldingcmax = cmax * (math.e ** (-zbase/z0))
            frictionCoef = max(foldingcmax, cmin)
        else:
            frictionCoef = cmax
    return frictionCoef
