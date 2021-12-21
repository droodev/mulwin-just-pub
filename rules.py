# copyright 2020 Andrzej Kaczmarczyk (andrzej >dot> kaczmarczyk <at> agh.edu.pl; a <dot> kaczmarczyk <at> tu-berlin.de)
# This file is part of mul-win-just-pub.
# mul-win-just-pub is licensed under the terms of MIT license
# see LICENSE.txt for the text of the lincense

from baseProgram import compute, COVERAGE_MAX, APPROVAL_MAX, compute_pav
from baseProgram import COMPUTE_PJR, COMPUTE_EJR, computeEJRorPJR
from gmpy2 import mpq
import sys
import tools

class JRCommittee(object):
  def compute(self, candidates, voters, mesh, stats, existenceSymbol):
    committeeSize = mesh.committeeSize
    mesh.clipMeshByValues(stats.minJRCov, stats.maxJRCov, stats.minJRApp, stats.maxJRApp)

    for cell in mesh.getUnclippedCells():
      lc, uc, la, ua = cell
      toOut='.'
#      print(lc, uc, la, ua )
      if compute(candidates, voters, la, ua, lc, uc, committeeSize)[0]:
        toOut=existenceSymbol
      mesh.setValueOfCell(cell, toOut)

class PJRCommittee(object):
  def compute(self, candidates, voters, mesh, stats, existenceSymbol):
    committeeSize = mesh.committeeSize
    mesh.clipMeshByValues(stats.minJRCov, stats.maxJRCov, stats.minJRApp, stats.maxJRApp)

    for cell in mesh.getUnclippedCells():
      lc, uc, la, ua = cell
      toOut='.'
      if computeEJRorPJR(candidates, voters, la, ua, lc, uc, committeeSize, COMPUTE_PJR)[0]:
        toOut=existenceSymbol
      mesh.setValueOfCell(cell, toOut)

class AnyCommittee(object):
  def compute(self, candidates, voters, mesh, stats, existenceSymbol):
    committeeSize = mesh.committeeSize
    mesh.clipMeshByValues(stats.minCov, stats.maxCov, stats.minApp, stats.maxApp)

    for cell in mesh.getUnclippedCells():
      lc, uc, la, ua = cell
      toOut='.'
#      print(lc, uc, la, ua )
      if compute(candidates, voters, la, ua, lc, uc, committeeSize, goal =
          APPROVAL_MAX, requireJR = False)[0]:
        toOut=existenceSymbol
      mesh.setValueOfCell(cell, toOut)

class MaxApprovalCommittee(object):
  def compute(self, candidates, voters, mesh, stats, existenceSymbol):
    committeeSize = mesh.committeeSize
    mesh.clipMeshByValues(stats.minCov, stats.maxCov, stats.maxApp, stats.maxApp)

    for cell in mesh.getUnclippedCells():
      lc, uc, la, ua = cell
      toOut='.'
#      print(lc, uc, la, ua )
      if compute(candidates, voters, la, ua, lc, uc, committeeSize, goal =
          COVERAGE_MAX, requireJR = False)[0]:
        toOut=existenceSymbol
      mesh.setValueOfCell(cell, toOut)

class ChambelinCourantCommittee(object):
  def compute(self, candidates, voters, mesh, stats, existenceSymbol):
    committeeSize = mesh.committeeSize
    mesh.clipMeshByValues(stats.maxCov, stats.maxCov, stats.minApp, stats.maxApp)

    for cell in mesh.getUnclippedCells():
      lc, uc, la, ua = cell
      toOut='.'
#      print(lc, uc, la, ua )
      if compute(candidates, voters, la, ua, lc, uc, committeeSize, requireJR = False)[0]:
        toOut=existenceSymbol
      mesh.setValueOfCell(cell, toOut)

class PAV(object):
  def compute(self, candidates, voters, mesh, stats, existenceSymbol):
    committeeSize = mesh.committeeSize
    mesh.clipMeshByValues(stats.minJRCov, stats.maxJRCov, stats.minJRApp, stats.maxJRApp)

    maxSatisfaction = SinglePAV().compute(candidates, voters, mesh, stats, existenceSymbol)

    for cell in mesh.getUnclippedCells():
      lc, uc, la, ua = cell
#      print(lc, uc, la, ua )
      if compute_pav(candidates, voters, la, ua, lc, uc, committeeSize,
          satisfactionLevel=maxSatisfaction)[0]:
        mesh.setValueOfCell(cell, existenceSymbol)

class SinglePAV(object):
  def compute(self, candidates, voters, mesh, stats, existenceSymbol):
    committeeSize = mesh.committeeSize
    success, satisfaction, _, coverage, approval = compute_pav(candidates, voters,
        stats.minJRApp, stats.maxJRApp, stats.minJRCov, stats.maxJRCov,
        committeeSize)
    if success:
      mesh.setValueOfCell(mesh.getCellFromValues(coverage, approval), existenceSymbol)
    return satisfaction

class SequentialPhragmen(object):

  def compute(self, candidates, voters, mesh, stats, existenceSymbol):
    committees = self.computeAllCommittees(candidates, voters, mesh.committeeSize)
    committeesWithAppAndCoverage = []
    for committee in committees:
      approvals, coverage = tools.committeApprovalAndCoverage(candidates, voters, committee)
      committeesWithAppAndCoverage.append((committee, approvals, coverage))
    self.depictMesh(committeesWithAppAndCoverage, existenceSymbol, mesh)


  def depictMesh(self, committees, existenceSymbol, mesh):
    for cell in mesh.getUnclippedCells():
      lc, uc, la, ua = cell
 #     print(lc, uc, la, ua )
      for _, coverage, approvalScore in committees:
        if coverage >= lc and coverage <= uc and approvalScore >= la and approvalScore <= ua:
          mesh.setValueOfCell(cell, existenceSymbol)
          break


  def computeAllCommittees(self, candidates, preferences, committeeSize):

    def __enough_approved_candiates():
      appr = set()
      for pref in preferences.values():
        appr.update(set(pref))
      if len(appr) < committeeSize:
        print("committeesize is larger than number of approved candidates")
        exit()

    __enough_approved_candiates()

    load = {vnr:0 for vnr in preferences.keys()}
    com_loads = {():load}
    
    approvers_weight = {}
    for c in candidates:
        approvers_weight[c] = sum(1 for v in preferences.values() if c in v)

#
    for _ in range(0, committeeSize):  # size of partial committees currently under consideration
        com_loads_next = {}
        for committee, load in iter(com_loads.items()):
            approvers_load = {}
            for c in candidates:
                approvers_load[c] = sum(load[vnr] for vnr, v in preferences.items() if c in v)
            new_maxload = [mpq(approvers_load[c] + 1, approvers_weight[c])
                            if approvers_weight[c] > 0 else len(candidates)*len(preferences)
                            for c in candidates]
            for c in candidates:
                if c in committee:
                    new_maxload[c] = sys.maxsize
            for c in candidates:
                if new_maxload[c] <= min(new_maxload):
                    new_load = {}
                    for vnr, v in preferences.items():
                        if c in v:
                            new_load[vnr] = new_maxload[c]
                        else:
                            new_load[vnr] = load[vnr]
                    com_loads_next[tuple(sorted(committee + (c,)))] = new_load
        # remove suboptimal committees, leave only the best branching_factor many (subject to ties)
        com_loads = {}
        cutoff = min([max(load) for load in com_loads_next.values()])
        for com, load in iter(com_loads_next.items()):
            if max(load) <= cutoff:
                com_loads[com] = load
    return [set(comm) for comm in com_loads.keys()]
