import numpy as np
from scipy.optimize import minimize as fminsearch
def pyGetAdjCT(targetpH, ABtable, IS):
    adjC = 0
    fhan = lambda adjC:CalcError(adjC, targetpH, ABtable, IS)#anon. function CalcError: python, found here
    return fminsearch(fhan, adjC, method='Nelder-Mead')

def CalcError(adjC, targetpH, ABtable, IS):
    phpred = CalcpH_ABT(ABtable,IS,adjC)
    return (targetpH - phpred)**2

def CalcpH_ABT(ABtable, IS, adjC):
    H = 1e-14
    tol = 1e-15
    maxevals = 1000
    Kw = 1e-14
    pKvals = ABtable[1]
    conc = ABtable[0]
    ab_chars = ABtable[2]
    ABmatrix = np.vstack((conc, adjpka(pKvals, IS)))
    rowCount = len(conc)
    for itr in range(maxevals):
        Fx = getFx(rowCount, ABmatrix, Kw, H, adjC, ab_chars)
        Fp = getFp(rowCount,ABmatrix,Kw,H)
        H -= (Fx/Fp)
        #print(f"Fx={np.round(Fx,3)}, Fp={Fp}, H={np.round(H,3)}, AdjC={np.round(adjC,3)}")
        if abs(Fx) < tol:
            break
    if H>=0 and itr < maxevals:
        return -np.log10(H)
    else:
        return -1

def getFx(rowCount, concpK, Kw, H, adjC, ab_chars):
    zval = (Kw/H) - H + adjC
    for i in range(rowCount):
        J = concpK[0][i]
        K = 10**(-concpK[1][i])
        if ab_chars[i] == "a":
            zval += K*J/(H+K)
        elif ab_chars[i] == "b":
            zval -= H*J/(H+K)
    return float(zval)

def getFp(rowCount, concpK, Kw, H):
    zval = -(Kw/(H**2))-1
    for i in range(rowCount):
        J = concpK[0][i]
        K = 10**-concpK[1][i]
        zval -= (J*K)/np.power(K + H, 2)
    return float(zval)

def adjpka(pKo, IS):
    b = 0.3
    A = 0.51
    sqrIS = np.sqrt(IS)
    temp = (sqrIS/(1+sqrIS))-b*IS
    pKa = pKo - 2*A*temp
    return pKa
