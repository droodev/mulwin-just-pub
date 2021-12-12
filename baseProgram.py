# copyright 2020 Andrzej Kaczmarczyk (andrzej >dot> kaczmarczyk <at> agh.edu.pl; a <dot> kaczmarczyk <at> tu-berlin.de)
# This file is part of mul-win-just-pub.
########################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
########################################################################

from gurobipy import *
import isxJRChecker

CANDIDATE_VARIABLE_NAME="cc"
COVERAGE_VARIABLE_NAME="coverage"
APPROVAL_VARIABLE_NAME="approvalScore"

COMM_OF_GIVEN_SIZE = 0
CORE_MIN = 1
APPROVAL_MAX = 2
APPROVAL_MIN = 3
COVERAGE_MAX = 4
COVERAGE_MIN = 5

COMPUTE_EJR = 0
COMPUTE_PJR = 1

def compute(candidates, voters, lab, uab, lcb, ucb, committeeSize,
    goal=COMM_OF_GIVEN_SIZE, requireJR=True):

  try:
    m = _basicModel(candidates, voters, lab, uab, lcb, ucb, committeeSize, goal, requireJR)
    m.optimize()
    
    if not m.Status == GRB.OPTIMAL:
      return False, None
    else:
      return True, int(m.objVal)
  except GurobiError:
    print('Error reported')

def computeEJR(candidates, voters, lab, uab, lcb, ucb, committeeSize):
    return computeEJRorPJR(candidates, voters, lab, uab, lcb, ucb, committeeSize, COMPUTE_EJR)

def computePJR(candidates, voters, lab, uab, lcb, ucb, committeeSize):
    return computeEJRorPJR(candidates, voters, lab, uab, lcb, ucb, committeeSize, COMPUTE_PJR)

def compute_pav(candidates, voters, lab, uab, lcb, ucb, committeeSize, satisfactionLevel = None):
  try:
    m = Model("MaxApproval")
    m.setParam('OutputFlag', False )

    indicatorVCOVars = m.addVars(len(voters), len(candidates), committeeSize, vtype=GRB.BINARY)
  
    candidateVars = m.addVars(candidates, name=CANDIDATE_VARIABLE_NAME, vtype=GRB.BINARY)
    
    voterVars = m.addVars(voters.keys(), name="vr", vtype=GRB.CONTINUOUS, lb=0.0, ub=1.0)

    coreSizeVar = m.addVar(name="coreSize", vtype=GRB.INTEGER, lb=0, ub=committeeSize)

    approvalScoreVar = m.addVar(name=APPROVAL_VARIABLE_NAME, vtype=GRB.INTEGER, lb=1)

    coverageVar = m.addVar(name=COVERAGE_VARIABLE_NAME, vtype=GRB.INTEGER, lb=1)

    satisfactionVar = m.addVar(name="satisfaction", vtype=GRB.CONTINUOUS, lb=1)

    m.addConstrs(indicatorVCOVars[i,j,k] <= candidateVars[j]
        for i in range(len(voters)) for j in range(len(candidates)) for k in range(committeeSize))

    m.addConstrs(indicatorVCOVars.sum(i,'*',k) == 1
        for i in range(len(voters)) for k in range(committeeSize))

    m.addConstrs(indicatorVCOVars.sum(i,j, '*') <= 1
        for i in range(len(voters)) for j in range(len(candidates)))

    m.addConstr(coreSizeVar == committeeSize)

    m.addConstr(quicksum(candidateVars[i] for i in candidates) == coreSizeVar)
    m.addConstrs((voterVars[j] <= quicksum(candidateVars[i] for i in voters[j])) for j in voters.keys())
    m.addConstrs((voterVars[j] >= candidateVars[i]) for j in voters.keys() for i in voters[j])

    m.addConstr(coverageVar == quicksum(voterVars[j] for j in voters.keys()))

    m.addConstr(coverageVar <= ucb)
    m.addConstr(coverageVar >= lcb)

    m.addConstr(approvalScoreVar == (quicksum(quicksum(candidateVars[i] for j in voters.keys() if i in
      voters[j]) for i in candidates)))

    m.addConstr(approvalScoreVar <= uab)
    m.addConstr(approvalScoreVar >= lab)

    coefficients = dict()
    for vnr, vote in voters.items():
      for cand in candidates:
        for k in range(committeeSize):
          owaCoeff =float(1/float(k+1))
          voterLikesCandidateCoeff = 1 if cand in vote else 0
          coefficients[(vnr, cand, k)]=owaCoeff*float(voterLikesCandidateCoeff)
    m.addConstr(indicatorVCOVars.prod(coefficients) == satisfactionVar)

    if satisfactionLevel == None:
      m.setObjective(satisfactionVar, GRB.MAXIMIZE)
    else:
      m.addConstr(satisfactionVar == satisfactionLevel)

    m.optimize()

    if not m.Status == GRB.OPTIMAL:
      return False, None, indicatorVCOVars, None, None
    else:
      return True, m.objVal, indicatorVCOVars, coverageVar.X, approvalScoreVar.X

  except GurobiError as GErr:
    print('Error reported: {}'.format(GErr))


def _basicModel(candidates, voters, lab, uab, lcb, ucb, committeeSize, goal, requireJR):
  def approvalMaximization():
    m.setObjective(approvalScoreVar, GRB.MAXIMIZE)

  def approvalMinimization():
    m.setObjective(approvalScoreVar, GRB.MINIMIZE)

  def coverageMaximization():
    m.setObjective(coverageVar, GRB.MAXIMIZE)

  def coverageMinimization():
    m.setObjective(coverageVar, GRB.MINIMIZE)

  def coreMinimization():
    m.setObjective(coreSizeVar, GRB.MINIMIZE)

  try:
    m = Model("MaxApproval")
    m.setParam('OutputFlag', False )
  
    candidateVars = m.addVars(candidates, name=CANDIDATE_VARIABLE_NAME, vtype=GRB.BINARY)
    
    voterVars = m.addVars(voters.keys(), name="vr", vtype=GRB.CONTINUOUS, lb=0.0, ub=1.0)

    coreSizeVar = m.addVar(name="coreSize", vtype=GRB.INTEGER, lb=0, ub=committeeSize)

    approvalScoreVar = m.addVar(name=APPROVAL_VARIABLE_NAME, vtype=GRB.INTEGER, lb=1)

    coverageVar = m.addVar(name=COVERAGE_VARIABLE_NAME, vtype=GRB.INTEGER, lb=1)

    if goal!=CORE_MIN:
      m.addConstr(coreSizeVar == committeeSize)

    m.addConstr(quicksum(candidateVars[i] for i in candidates) == coreSizeVar)
    m.addConstrs((voterVars[j] <= quicksum(candidateVars[i] for i in voters[j])) for j in voters.keys())
    m.addConstrs((voterVars[j] >= candidateVars[i]) for j in voters.keys() for i in voters[j])

    if requireJR:
      smallerThanCohesiveSize = int(math.ceil(float(len(voters))/float(committeeSize)-1))
      m.addConstrs((quicksum(1-voterVars[j] for j in voters.keys() if i in
        voters[j]) <= smallerThanCohesiveSize  for i in candidates))

    m.addConstr(coverageVar == quicksum(voterVars[j] for j in voters.keys()))

    m.addConstr(coverageVar <= ucb)
    m.addConstr(coverageVar >= lcb)

    m.addConstr(approvalScoreVar == (quicksum(quicksum(candidateVars[i] for j in voters.keys() if i in
      voters[j]) for i in candidates)))

    m.addConstr(approvalScoreVar <= uab)
    m.addConstr(approvalScoreVar >= lab)

    if goal==COMM_OF_GIVEN_SIZE or goal==CORE_MIN:
      coreMinimization()
    if goal==APPROVAL_MAX:
      approvalMaximization()
    if goal==APPROVAL_MIN:
      approvalMinimization()
    if goal==COVERAGE_MAX:
      coverageMaximization()
    if goal==COVERAGE_MIN:
      coverageMinimization()

    return m

  except GurobiError as GErr:
    print('Error reported: {}'.format(GErr))

def _computeEJRorPJR(candidates, voters, lab, uab, lcb, ucb, committeeSize, whatToCompute,
    goal=COMM_OF_GIVEN_SIZE):
  xJRCheckers = {
        COMPUTE_EJR: isxJRChecker.isEJR_ilp,
        COMPUTE_PJR: isxJRChecker.isPJR_ilp
      }
  if whatToCompute not in [COMPUTE_EJR, COMPUTE_PJR]:
    raise ValueError("Neither ejr nor pjr requested. Use constants to specify a correct goal.")

  
  try:
    m = _basicModel(candidates, voters, lab, uab, lcb, ucb, committeeSize, goal, True)
    while True:
      m.optimize()
      if not m.Status == GRB.OPTIMAL:
        return False, None
      else:
        committee = []
        committeeVars = []
        for candId in candidates:
          candVar = m.getVarByName("{}[{}]".format(CANDIDATE_VARIABLE_NAME, candId))
          if int(round(candVar.X,0)) == 1:
            committee.append(candId)
            committeeVars.append(candVar)
        logging.debug(f"Checking commitee {committee} for EJR/PJR")
        votersAsBinaryMatr = isxJRChecker.appListsProfilesToBinaryMatrix(voters.values(),
            candidates)
        if xJRCheckers[whatToCompute](votersAsBinaryMatr, committee):
          return True, int(m.objVal)
        m.addConstr(quicksum(committeeVars) <= len(committeeVars)-1)
  except GurobiError as e:
    print('Error reported: ' + str(e))


