import numpy as np
import pandas as pd
from scipy.optimize import Bounds, minimize as fmincon
from decimal import Decimal, localcontext, ROUND_HALF_UP


def pyModelBCCurve(order, NpKs, minConc, pK_tol, NaClpercent, LB, UB, X, Y):#Equivalent of part of app.ModelBCCurveButtonPushed
    res = SCBC_fit(X, Y, order)#get trig data: python, found below
    scbcpred = res["Pred"]
    psize = scbcpred.shape#number of data pts
    indxvec = splitvec(NpKs, psize[0])#python, found below
    #initialize temporary matrix for initial conc-pK values
    tempMat = np.zeros((NpKs, 2))
    for k in range(NpKs):#for each pK assign:
        tempMat[k] = scbcpred[indxvec[k], ::-1]#The BC and pK values
    SPX = SimplexBCPK_DF5(scbcpred, tempMat, minConc, pK_tol, LB, UB)#python, fminconpy.py
    letters = getAB_letters(SPX["ABmat"])#python, found below
    buftable = []#Build the table
    buftable.append(SPX["ABmat"][:, 0].tolist())
    buftable.append(SPX["ABmat"][:, 1].tolist())
    buftable.append(letters)
    buftable.append(SPX["BCmat"][:, 0].tolist())
    minpH = np.amin(scbcpred[:,0])
    maxpH = np.amax(scbcpred[:,0])
    waterNaCl = NaClpercent/5.84#ask about why, in the original code, this is app.NaClpercentEditField.Value and not app.ParamTable.Value('NaClPercent')
    tBetainfo = get_tBetaData(SPX["ABmat"], minpH, maxpH, waterNaCl, 0)
    return buftable, tBetainfo, SPX

def SCBC_fit(X, Y, order, calcArea=False):#Generic version of SCBCfit_only & SCBCfit_area
    #assignments
    res = {"Obs":None, "Pred":None, "params":None, "SSE":None, "recip_cond":None, "determinant":None, "area":None}
    mul = 0.5#X val multiplier (for 1 cycle 2..12)
    modelX = np.linspace(np.amin(X), np.amax(X), 100)#pred X: 100 pts between 2..12
    terms = 2*order + 1#b0 + 2 terms (for "degree" or "harmonic")
    N = len(X)#number of X data points

    #set up partial deriv matrix with summed sin, cos terms
    #get a vector (termsxN) with 2*order + 1 number of sine - cosine 
    # terms (with initial 1) and appropriate multiplier
    k = 1#matrix row index, skip first row (all 1s)
    #get matrix of X for each deriv
    factormat = np.ones((terms, N))#one row of X vals for each term 
    for j in range(1, order+1):#for each set of terms (order)
        factormat[k,:] = np.sin(j*mul*X)#sine term (times order index and mult.)
        factormat[k+1,:] = np.cos(j*mul*X)#cosine term (times order index and mult.)
        k+=2#advance row index
    pmat = np.zeros((terms,terms));          #square matrix for partial derivatives
    for l in range(terms):#for each row of square matrix (L not 1)
        for m in range(terms):#for each col of square matrix
            pmat[l,m] = np.dot(factormat[l,:],factormat[m,:])#sum sin and/or cos

    #get Y vector
    ymat = np.zeros(terms)#col vector for Y vals * each term
    for n in range(terms): #for each term mult Y val * sin or cos
        ymat[n] = np.dot(factormat[n,:], Y) #sum: SorC (col) * Y vals (col)
    #matrix division to calc params for sine-cosine model
    params = np.linalg.solve(pmat, ymat)#divide Y matrix by square param matrix
    if calcArea:#Only run this part to be like SCBCfit_area
        #This if statement is equivalent to CalcArea from SCBCfit_area
        loopvar = int((len(params) - 1)/2)#loop for each set of terms (but not Bo)
        b0 = params[0]#set Bo
        p = 1#counter for param index
        minX = np.amin(X)
        maxX = np.amax(X)
        evalMin = 0#to sum min X answer
        evalMax = 0#to sum max X answer
        for i in range(1, loopvar):
            evalMin += (params[p+1]*np.sin(i*mul*minX) - params[p]*np.cos(i*mul*minX))/(i*mul)
            evalMax += (params[p+1]*np.sin(i*mul*maxX) - params[p]*np.cos(i*mul*maxX))/(i*mul)
            p+=2
        evalMin += b0*minX
        evalMax += b0*maxX
        evalArea = evalMax - evalMin
        return evalArea
    
    def CalcSCModel(currPrms, Xvals):#Equivalent of CalcSCModel from SCBCfit_only.m
        #calc model with final params and predicted X values
        loopvar = int((len(currPrms) - 1)/2)
        b0 = currPrms[0]
        p = 1
        sumterms = np.zeros(len(Xvals))
        for i in range(1, loopvar+1):
            sumterms += currPrms[p]*np.sin(i*mul*Xvals) + currPrms[p+1]*np.cos(i*mul*Xvals)
            p += 2
        return b0 + sumterms

    modelY = CalcSCModel(params,modelX)#calc predicted vals for each model X
    predY = CalcSCModel(params, X)#uses obs X values for this
    SSE = np.sum(np.power(Y - predY,2))#sum squared errors, predicted minus Y
    Obs = np.transpose(np.vstack((X, Y)))
    Pred = np.transpose(np.vstack((modelX, modelY)))
    res["Obs"] = Obs#BC Curve
    res["Pred"] = Pred#predicted (SCBC) model data
    res["params"] = params
    res["SSE"] = SSE#sum sq. error term
    res["recip_cond"] = np.linalg.cond(pmat)#matrix condition
    res["determinant"] = np.linalg.det(pmat)#determinant
    return res


def splitvec(byN, vecsize):#Equivalent of splitvec from splitvec.m
    indices = np.zeros(byN)#initialize return vector
    increment = vecsize/(byN + 1)#calc increment between values
    previous = 0#initialize previous index value
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP#Without this, UGH would be rounded to the nearest even number if it had a decimal of 0.5
        for i in range(byN):#for each index in the vector
            UGH = previous + increment#get int value for next index
            indices[i] = int(Decimal(UGH).to_integral_value())#Round it and turn it into an integer
            previous = indices[i]#reset previous value
    return indices.astype(int) - 1


def getAB_letters(abmat):#Equivalent of app.getAB_letters
    #Get "a" or "b" letters for acid or base
    rows, cols = abmat.shape#get size of matrix
    letters = ['a']*rows#make a char vec
    for i in range(rows):#for each buffer
        if abmat[i, 1] > 7:#check pH
            letters[i] = 'b'#reset if above 7
    return letters


def get_tBetaData(ABmat,pHmin,pHmax,waterIS,crvIS):#Equivalent of get_tBetaData from get_tBetaData.m
    tbetainfo = {"BCCurve":None, "waterCurve":None, "pHvec":None, "bctBeta":None, "watertBeta":None, "tBeta":None}
    waterNaClpct = waterIS*5.84
    crvNaClpct = crvIS*5.84
    pHvec = np.arange(pHmin, pHmax + 0.001, 0.05)
    bc = BetaModel_AB(ABmat, crvNaClpct, pHvec)#python, EventsFile.py
    wtr = BetaModel_AB(np.zeros((1,2)), waterNaClpct, pHvec)
    tbetainfo["BCCurve"] = bc
    tbetainfo["waterCurve"] = wtr
    tbetainfo["pHvec"] = pHvec
    tbetainfo["bctBeta"] = 100*SCBC_fit(bc[:,0], bc[:,1], 15, True)
    tbetainfo["watertBeta"] = 100*SCBC_fit(wtr[:,0], wtr[:,1], 15, True)
    tbetainfo["tBeta"] = tbetainfo["bctBeta"] - tbetainfo["watertBeta"]
    return tbetainfo



def SimplexBCPK_DF5(ObsXY, ABmat, minConc, pK_tol, LB, UB):#Equivalent of SimplexBCPK_DF5 from SimplexBCPK_DF5.m
    #assignments
    SPX = {"ABmat":None, "BCmat":None, "Pred":None, "SSE":None, "Obs":None}
    ObsX = ObsXY[:,0]#pH values (col)
    ObsY = ObsXY[:,1]#BC values (col)
    zeroflag = False#bool for check for no buffers
    PredX = ObsX#x value vector
    salt = 0#all calc done without IS correction
    ABmat = ABmat[abs(ABmat[:,0])>minConc, :]#keep values that meet condition for minimum conc in AB
    if ABmat.size == 0:#check for empty matrix
        ABmat = np.zeros((1, 2))#if empty, just use zeros
        zeroflag = True#set a flag so fit only water?
    else:
        ABmat = combineABs(ABmat, pK_tol)#combine rows w/similar pKs

    #set up boundry values for fmincon constraints on each parameter value
    row, col = ABmat.shape#get size of ABmat
    lowerBounds = np.zeros((row, col))#LB matrix, conc values remain zero 
    lowerBounds[:, 1] = LB#LB pKs have min of titration curve
    upperBounds = np.ones((row, col))#UB matrix, conc values have max of 1 M/L 
    upperBounds[:, 1] = UB#UB pKs have max of titration curve
    def ABmat2paramvec(paramValues):#Equivalent of ABmat2paramvec from SimplexBCPK_DF5.m
        #Convert AB matrix to linear vector conc;pK in order
        return paramValues.flatten('F')
    lbvec = ABmat2paramvec(lowerBounds)#convert matrix to vector (subfunc)
    ubvec = ABmat2paramvec(upperBounds)#convert matrix to vector (subfunc)

    #set up parameters for fmincon optimization
    paramvec = ABmat2paramvec(ABmat)
    fhan = lambda p:CalcSSE(p, salt, ObsX, ObsY)#anon. function SSE: python, found here
    bound = Bounds(lbvec, ubvec)#Define bounds for optimization
    #scipy.optimize.minimize is equivalent to fmincon from MATLAB in this instance
    res = fmincon(fhan, paramvec, tol=1e-20, bounds=bound, method="trust-constr")#optimize with constraints

    #regenerate AB matrix
    ABmat_pred = paramvec2ABvals(res.x)#convert linear vector to ABmat: python, found here
    #adjust AB matrix (remove very small or neg values and combine like pKs)
    ABmat_pred = ABmat_pred[abs(ABmat_pred[:,0])>minConc, :]#keep values that meet condition for minimum conc in AB
    ABmat_pred = combineABs(ABmat_pred, 0.3)#combine rows w/similar pKs

    #set pred data
    if zeroflag:
        ABmat_pred = np.zeros((1, 2))
    #Predicted data with BetaModel
    SPX["Pred"] = BetaModel_AB(ABmat_pred,salt, PredX)#returns Nx2 (pH,BC)
    if any(ABmat_pred[:,0] == 0):#dont call with a zero conc row
        SPX["BCmat"] = np.zeros((1,2))#return 1x2 zero matrix
    else:
        SPX["BCmat"] = Conc2Beta(ABmat_pred)#get beta values from AB matrix
    SPX["Obs"] = ObsXY#Nx2 (pH vector, BC)
    SPX["ABmat"] = ABmat_pred#Nx2 output (pred conc, pKvals)
    SPX["SSE"] = res.fun/20#scalar (sum sq err, recorrect)
    return SPX

def CalcSSE(paramvec, salt, ObsX, ObsY):#Equivalent of CalcSSE from SimplexBCPK_DF5.m
    ABvalues = paramvec2ABvals(paramvec)#python, found below
    Pred = BetaModel_AB(ABvalues, salt, ObsX)#python, EventsFile.py
    return 20*np.sum(np.power(ObsY - Pred[:,1], 2))

def paramvec2ABvals(paramvec):#Equivalent of paramvec2ABvals from SimplexBCPK_DF5.m
    #Convert linear conc;pK params back to AB matrix 
    num_rows = int(len(paramvec)/2)#get index for 1/2 of vector
    ABvals = np.zeros((num_rows, 2), dtype=float)
    ABvals[:, 0] = paramvec[:num_rows]#conc vals in 1st col
    ABvals[:, 1] = paramvec[num_rows:]#pK vals in 2nd col
    return ABvals

def combineABs(ABmat, tol):#Equivalent of CombineABs from CombineABs.m
    row, col = ABmat.shape#get number of AB pairs
    newABmat = np.zeros((row, col))
    newABmat[0, :] = ABmat[0,:]#new AB mat with 1st val
    index = 0#Index for new ABmat
    if row > 1:
        for i in range(1, row):
            if abs(ABmat[i,1] - ABmat[i-1,1]) < tol:#if next with tol of prev
                temp_conc = ABmat[i,0] + newABmat[index,0]#get new conc
                newABmat[index, 0] = temp_conc#set new value to new AB mat
            else:
                index += 1#advance index
                newABmat[index,:] = ABmat[i,:]#pK values different, so use
    return newABmat[:index+1, :]

def Conc2Beta(ABmat):#Equivalent of Conc2Beta from Conc2Beta.m
    #get number of rows in ABmat, set up return matrix
    rows, cols = ABmat.shape#rows in ABmat
    NaClPercent = 0#don't alter pK due to salt
    temp = np.zeros((rows, 2))#return matrix
    #for each row, calculate the beta value for the corresponding pH
    for i in range(rows):
        temp[i, :] = BetaModel_AB(ABmat[i,:], NaClPercent, np.array(ABmat[i, 1], ndmin=1))#python, EventsFile.py
    #BetaModel returns pH, BC: we want BC, pH
    return temp[:,::-1]
    
    return WC
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

def AdjustpKaMonoprotic(pKo, I, TempC):
    b = 0.3
    epsilon = 78.3808
    degK = TempC + 273
    A = 1.825*(10**6)*np.power(epsilon*degK, -3/2)
    temp = -b*I + np.sqrt(I)/(1+np.sqrt(I))
    return pKo - 2*A*temp

