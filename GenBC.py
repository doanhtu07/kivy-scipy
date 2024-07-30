import numpy as np
def pyGenBCCurve(init_vol, molHCl, molNaOH, removeVal, mingaps, increment, acid_x, acid_y, base_x, base_y): #a fusion of Data2Beta and the plotting function in the app
    D2B = {"init_vol":None,"init_pH_acid":None,"acid":None,"init_pH_base":None,"base":None, "BC":None}#The same res collected by Data2Beta.m
    #report initial pH values for acid titraiton and base titration
    D2B["init_vol"] = init_vol                          #initial titration vol in L
    D2B["init_pH_acid"] = acid_x[1]                     #initial pH, acid titraiton
    acid = tCurve(acid_x, acid_y, molHCl, init_vol)     #python, found below
    acid[:,6] = range(len(acid_x),0,-1)                 #Index, num backwards for acid data
    D2B["acid"] = acid                #Save copy acid data before adjust for BC curve
    D2B["init_pH_base"] = base_x[1]                     #initial pH, base titration
    base = tCurve(base_x, base_y, molNaOH, init_vol)    #python, found below
    base[:,6] = np.arange(1,len(base_x)+1) + len(acid_x)#Index, num from acid val
    D2B["base"] = base                #Save copy base data before adjust for BC curve

    #%remove 1st two pts (start of titration 0 vals + 1)
    acid = np.delete(acid, range(2), 0)#remove junction values based on 0 vol
    base = np.delete(base, range(2), 0)#remove junction values based on 0 vol

    #flip the acid titration and append base titration
    BC = np.vstack((np.flipud(acid), base))
    #use logical indexing to remove rows w/specific condition (3rd col < val)
    TF = BC[:,2] < removeVal#generate True-False vector (TF)
    BC = np.delete(BC, TF, 0)#adjust matrix by logical val

    #reformat BC data
    BC[:,0]=BC[:,1]#pH values to 1st col
    BC[:,1]=BC[:,5]#Calc BC vals to 2nd col
    BC = np.delete(BC, range(2,7), 1)#delete rest of matrix
    oriBC = BC
    D2B["BC"] = oriBC

    fillBC = fillGaps(oriBC, mingaps, increment)#python, found below
    return D2B, oriBC, fillBC

def tCurve(titr_x, titr_y, molarity, init_vol):
    #get BC results for each titration and add index values for each data set
    vols = [x / 1000 for x in titr_x]          #convert accum added vols to liters(L)
    nvals = len(vols)            #get number of data points
    rval = np.zeros((nvals, 7))  #set up return matrix
    rval[:,0] = [vol + init_vol for vol in vols]  #convert to total accum vol (L)
    rval[:,1] = titr_y           #assign pH values for each step
    for i in np.arange(1, nvals):                  #for all additions of titrant:
        rval[i, 2] = abs(rval[i, 1]-rval[i-1, 1])  #delta pH 
        rval[i, 3] = vols[i] - vols[i-1]           #delta vol of added titrant
        rval[i, 4] = rval[i, 3]*molarity/rval[i, 0]#delta M/L titrant in sol
        if rval[i, 2] != 0:                        #zero division = bad
            rval[i, 5] = rval[i, 4]/rval[i, 2]     #calc BC = dC/dpH
    #convert units for acid/base and format output data
    #This was originally in Data2Beta, but I decided to move it here for simplicity
    rval[:,0] = np.around(rval[:,0]*1000,4)   #L to ml total vol
    rval[:,1] = np.around(rval[:,1],4)        #pH
    rval[:,2] = np.around(rval[:,2],4)        #delta pH
    rval[:,3] = np.around(rval[:,3]*1000000,0)#L to ul vol added
    rval[:,4] = np.around(rval[:,4]*1000,4)   #M/L to mM/L delta acid 
    rval[:,5] = np.around(rval[:,5],4)        #BC Value
    return rval

def fillGaps(BCCurve, mingaps, increment):#Equivalent to FillGaps from FillGaps.m
    #scroll through BC curve and find all gaps larger than mingap
    gapList = findGaps(BCCurve, mingaps)#python, found below
    if np.all(gapList == 0):            #check to see if gaps existed
        return BCCurve                  #just return original function, end function if no gaps
    rows, cols = gapList.shape          #get number of gaps in the list
    fillBC = BCCurve[:]#set up new BC curve, return matrix

    #process gap list and add fills to newBC curve
    for row in range(rows):#for each gap
        tempStart = gapList[row][1]                         #get the starting pH
        tempEnd = gapList[row][2]                           #get the end pH 
        #generate vector with x values for gap
        xvalvec = get_xValVec(tempStart, tempEnd, increment)#python, found below
        xvals = gapList[row][range(1,3)]                    #pH vals for gap start and end
        yvals = gapList[row][range(3,5)]                    #BC vals for gap start and end
        #get the slop and intercept of the line between gap start-end points
        lineSlope, lineIntercept = get_lineParams(xvals, yvals)#python, found below
        #now, get Y values for points on line at each xvalvec
        yvalvec = lineSlope*xvalvec + lineIntercept
        #make xy vectors into Nx2
        newInputs = np.hstack((xvalvec[:, np.newaxis], yvalvec[:, np.newaxis]))
        fillBC = np.vstack((fillBC,newInputs))
    #sort new BC curve with filled gap data by pH values
    ind = np.argsort(fillBC[:,0])
    fillBC = fillBC[ind]
    TF = [x in BCCurve for x in fillBC]
    return np.delete(fillBC, TF, 0)


def findGaps(BCCurve, mingapsize):#Equivalent to FindGaps from FillGaps.m
    xvals = BCCurve[:,0]#X val vector
    yvals = BCCurve[:,1]#Y val vector
    xlen = len(xvals)#length (scalar)
    gapVec = np.zeros((xlen-1,3))#Nx2 of start index and gaps

    #Determine gap size
    for i in range(xlen-1):#for each gap in list
        gapVec[i,0] = i#start index for each gap
        gapVec[i,1] = i+1#end index for each gap
        gapVec[i,2] = xvals[i+1] - xvals[i]#gend index for each gap

    #sort gap vector largest gap to smallest
    ind = np.argsort(gapVec[:,2])#largest gaps at begining
    gapVec = gapVec[ind[::-1]]
    ngaps = 0
    gapList = np.zeros((xlen-1, 5))
    #build return matirx with only gaps that are larger than mingap size
   
    for i in range(xlen-1):              #scroll through gap list
        if gapVec[i,2] > mingapsize:     #check gap size
            ind_start = int(gapVec[i, 0])#if too big, start val index
            ind_end = int(gapVec[i, 1])  #assign end val index
            gapList[i,:] = [ind_start, xvals[ind_start], xvals[ind_end], yvals[ind_start], yvals[ind_end]]#x and y vals
            ngaps+=1
        else:#remaining gaps too small
            break
    if ngaps == 0:#if no gaps
        return np.zeros((1,5))#return one row of zeros
    return gapList[:ngaps, :]

def get_xValVec(startval, endval, increment):#Equivalent to GetXvalVec from FillGaps.m
    #Get a check for in case increment is changed to 0 somehow
    #get a vector of x values (pH values) across gap for each increment
    tempval = startval          #starting pH
    ind = 0                     #temp index
    xvec = []
    while True:                 #loop till end pH reached
        tempval += increment    #increment pH
        if tempval < endval:    #check for end value
            xvec.append(tempval)#assign next pH value
            ind+=1              #next index for vector
        else:                   #end pH reached, finish loop
            return np.array(xvec)

def get_lineParams(xs, ys):#Equivalent to GetLineParams from FillGaps.m
    #generate slope, intercept parameters for line from two XY points
    slope = np.diff(ys)/np.diff(xs)#calc slope
    intercept = ys[0] - slope*xs[0]#calc intercept
    return slope, intercept        #return line parameters