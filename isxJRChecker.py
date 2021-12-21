#!/usr/bin/python3

# copyright 2020 Andrzej Kaczmarczyk (andrzej >dot> kaczmarczyk <at> agh.edu.pl; a <dot> kaczmarczyk <at> tu-berlin.de)
# This file is part of mul-win-just-pub.
# mul-win-just-pub is licensed under the terms of MIT license
# see LICENSE.txt for the text of the lincense

from pulp import *
import math

def appListToBinaryVector(voter, candidates):
  v = [1 if c in voter else 0 for c in candidates]
  return v

def appListsProfilesToBinaryMatrix(voters, candidates):
  return [appListToBinaryVector(voter, candidates) for voter in voters]

def mostPopular( V ):
    m = len(V[0])
    n = len(V)
    M = 0
    M_c = -1
    for c in range(m):
        count = sum( [V[i][c] for i in range(n) ] )
        if count > M:
            M = count
            M_c = c
    return (M_c,M)

def removeVoters( V, c ):
    Vnew = []
    for v in V:
        if v[c] == 0:
            Vnew += [v]
    return Vnew

def baseXJR_ilp( V, W, ell ):
  n = len(V)
  m = len(V[0])
  k = len(W)

  noverk = n/k
  ### BELOW: there is indeed problem with division
  ### but we take ceiling in our ILP, so I commented
  ### this part out
  #if( noverk * k != n ):
  #  print "Problem with division!"

  model = LpProblem( "EJR", LpMinimize)

  X = [LpVariable( "x%d" % i, cat = "Binary" ) for i in range(n)]
  Y = [LpVariable( "y%d" % j, cat = "Binary" ) for j in range(m)]

  # choose ell*noverk voters
  model += lpSum(X) == math.ceil(ell*noverk)
  # choose ell candidates that will witness cohesiveness
  model += lpSum(Y) == ell

  #ensure all chosen candidates are approved by all selected voters
  for i in range(n):
    for j in range(m):
      model += Y[j] <= V[i][j] + (1-X[i])

  return (model,X,Y)

def pjr_ilp( V, W, ell ):
  n = len(V)
  k = len(W)
  (model, X,Y) = baseXJR_ilp( V, W, ell )

  WW = [LpVariable( "w%d" % j, cat = "Binary" ) for j in range(k)]

  for j in range(k):
    for i in range(n):
      model += WW[j] >= X[i]*V[i][W[j]]
    model += WW[j] <= lpSum( [X[i]*V[i][W[j]] for i in range(n)] )

  model += lpSum( WW ) <= ell-1


  return (model,X,Y)




def isPJR_ilp( V, W ):
  n = len(V)
  k = len(W)

  for ell in range(1,k+1):
#    print "Testing PJR", ell
    (model,X,Y) = pjr_ilp( V, W, ell )
    model.solve(GUROBI(msg=0))
    if( model.status == 1 ):
#      print "NO PJR"
      return False  

# print "Is PJR"
  return True

def ejr_ilp( V, W, ell ):
  n = len(V)
  m = len(V[0])
  (model, X,Y) = baseXJR_ilp( V, W, ell )

  for i in range(n):
    approved = 0
    for j in W:
      approved += V[i][j]
    model +=  m*(1-X[i]) >= approved -  ell + 1

  return (model,X,Y)

def isEJR_ilp( V, W ):
  n = len(V)
  k = len(W)


  for ell in range(1,k+1):
#    print "Testing EJR", ell
    (model,X,Y) = ejr_ilp( V, W, ell )
    model.solve(GUROBI(msg=0))
    if( model.status == 1 ):
#      print "NO EJR"
      return False  # comment out for the ILP to provide explanation about failing EJR

      print ("ILP STATUS = " + LpStatus[model.status])


      for j in range(m):
        if Y[j].value() > 0:
          print ("Witnessing candidate: {}, {}".format(j,Y[j].value()))

      for i in range(n):
        if X[i].value() > 0:
          s = "voter %d: " % i
          for j in range(m):
            if Y[j].value() > 0:
              s += "c%d: %d  " % (j,V[i][j])
          print (s)
 
      S = []
      for i in range(n):
        if X[i].value() > 0:
          s = ""
          for j in W:
            s += "V[%d][%d] = %d  " % (i,j, V[i][j] ) 
          print(s)
          S += [i]
      print (f"Failing voters: {S}")
      print (f"W: {W}")

      return False 

#  print "is EJR"
  return True
def isJR( V, W ):
    n = len(V)
    k = len(W)
    for c in W:
        V = removeVoters(V, c)

    if len(V) == 0 :
        return True

    (c,M) = mostPopular( V )
    if M >= float(n)/float(k):
        return False
    return True 

def xJRChecking(V, W):
  '''This functions checks whether a profile is ERJ, PJR, and JR.
     It returns a boolean-valued triplet (JR, EJR, PJR) where an entry
     is True when the committee meets a respeective xJR'''
  JRFlag = isJR(V, W)
  if not JRFlag:
    return(False, False, False)
  A = isEJR_ilp(V, W)
  if A:
    return(True, True, True)
  A = isPJR_ilp(V, W)
  if A:
    return(True, True, False)
  return (True, False, False)
