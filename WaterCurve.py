import numpy as np

def genWater( maxBC, NaClpercent, start, finish, start_inc = 0.075, finish_inc = 0.1, epsilon = 0.0001, step = 0.05):
    ABmat = np.zeros((1, 2))
    for i in range(1, 11):
        waterpHvec = np.arange(start, finish+epsilon, step)
        WaterCurve = BetaModel_AB(ABmat, NaClpercent, waterpHvec)
        maxWC = np.amax(WaterCurve[:,1])
        if maxWC < 1.7*maxBC:
            break
        else:
            start += i*start_inc
            finish -= i*finish_inc
    
    return WaterCurve
    
def BetaModel_AB(ABmat, NaClpercent, pHvec):
    if ABmat.ndim > 1:
        Conc = ABmat[:,0]
        pKa = ABmat[:,1] 
    else:
        Conc = np.array(ABmat[0], ndmin=1)
        pKa = np.array(ABmat[1], ndmin=1)
    const = 2.302585 #natural log of 10
    Temp = 25
    IonicStr = NaClpercent/5.84
    Kw = 10**-AdjustpKaMonoprotic(14, IonicStr, Temp)
    pKa = AdjustpKaMonoprotic(pKa, IonicStr, Temp)
    Ka = 10**-pKa
    num_buffers = np.amax(np.shape(Conc))
    H = 10**-pHvec
    num_pHvals = np.amax(np.shape(pHvec))
    OH = Kw/H
    buffvecs = np.zeros((num_pHvals, num_buffers))
    BCCurve = np.zeros((num_pHvals, 2))
    for j in range(num_buffers):
        buffvecs[:,j] = Conc[j]*Ka[j]*H/np.power(H+Ka[j], 2)
    buffsum = np.sum(buffvecs, 1)
    BCCurve[:,0] = pHvec
    BCCurve[:,1] = const*(buffsum + OH + H)
    return BCCurve

def AdjustpKaMonoprotic( pKo, I, TempC):
    b = 0.3
    epsilon = 78.3808
    degK = TempC + 273
    A = 1.825*(10**6)*np.power(epsilon*degK, -3/2)
    temp = -b*I + np.sqrt(I)/(1+np.sqrt(I))
    return pKo - 2*A*temp