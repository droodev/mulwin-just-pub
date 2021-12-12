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

import random
import math
import csv

class VotesGenerator(object):
  def generate(self, candidates):
    pass
  def description(self):
    pass

class ParameterizedGenerator(VotesGenerator):
  def parameters(self):
    pass

class MallowsModel(ParameterizedGenerator):
  def __init__(self, inTargetCommitteeProbability, targetCommitteeSize):
    self._inTargetCommProb = inTargetCommitteeProbability
    self._targetCommSize = targetCommitteeSize

  def generate(self, candidates, votersnr):
    def genSingleVoter():
      vote = []
      for c in targetCommittee:
        if random.random() < self._inTargetCommProb:
          vote.append(c)
      for c in set(candidates).difference(set(targetCommittee)):
        if random.random() > self._inTargetCommProb:
          vote.append(c)
      return vote
    targetCommittee = random.sample(candidates, self._targetCommSize)
    votes = {}
    for i in range(votersnr):
      votes[i] = genSingleVoter()
    return candidates, votes

  def description(self):
    return "Mallows Model, probability: {}, committee size: \
      {}".format(self._inTargetCommProb, self._targetCommSize)

  def parameters(self):
    return (self._inTargetCommProb, self._targetCommSize)

class EqualChooseDistribution(ParameterizedGenerator):
  def __init__(self, approvalProbability):
    self._approvalProbability = approvalProbability

  def generate(self, candidates, votersnr):
    votes = {}
    for i in range(votersnr):
      vote = []
      for c in candidates:
        if random.random() < self._approvalProbability:
          vote.append(c)
      votes[i]=vote
    return candidates, votes
  
  def description(self):
    return "Impartial, probability: {}".format(self._approvalProbability)
  
  def parameters(self):
    return (self._approvalRadius,)


class OneDDistribution(ParameterizedGenerator):
  def __init__(self, approvalRadius):
    self._approvalRadius = approvalRadius

  def generate(self, candidates, votersnr):
    votersPositions = []
    candidatesPositions = []
    for i in xrange(votersnr):
      votersPositions.append(random.uniform(0,1))
    for i in xrange(len(candidates)):
      candidatesPositions.append(random.uniform(0,1))
    votes = {}
    for i in range(votersnr):
      vote = []
      maxApproved = votersPositions[i]+self._approvalRadius
      minApproved = votersPositions[i]-self._approvalRadius
      for c in xrange(len(candidates)):
        if candidatesPositions[c] <= maxApproved and candidatesPositions[c] >= minApproved:
          vote.append(c)
      votes[i]=vote
    return candidates, votes

  def description(self):
    return "1D, radius: {}".format(self._approvalRadius)

  def parameters(self):
    return (self._approvalRadius,)


class TwoDDistribution(ParameterizedGenerator):
  def __init__(self, approvalRadius):
    self._approvalRadius = approvalRadius

  def generate(self, candidates, votersnr):

    votersPositions = []
    candidatesPositions = []
    for i in xrange(votersnr):
      votersPositions.append((random.uniform(0,1), random.uniform(0,1)))
    for i in xrange(len(candidates)):
      candidatesPositions.append((random.uniform(0,1), random.uniform(0,1)))
    votes = {}
    for i in range(votersnr):
      vote = []
      vx = votersPositions[i][0]
      vy = votersPositions[i][1]
      for c in xrange(len(candidates)):
        cx = candidatesPositions[c][0]
        cy = candidatesPositions[c][1]
        if math.hypot(vx - cx, vy - cy) <= self._approvalRadius:
          vote.append(c)
      votes[i]=vote
    return candidates, votes

  def description(self):
    return "2D, radius: {}".format(self._approvalRadius)

  def parameters(self):
    return (self._approvalRadius,)
    
class UrnModel(VotesGenerator):
  def __init__(self, approvalProbability, numberOfReturned):
    self._numberOfReturned = numberOfReturned
    self._approvalProbability = approvalProbability

  def generate(self, candidates, votersnr):
    urn = list(candidates[:])
    votes = {}
    for i in range(votersnr):
      voteCandidates = 0
      for c in candidates:
        if random.random() < self._approvalProbability:
          voteCandidates = voteCandidates + 1
      localUrn = urn[:]
      vote = []
      for _ in range(voteCandidates):
        approvedCandidate = random.choice(localUrn)
        vote.append(approvedCandidate)
        localUrn = [c for c in localUrn if not c == approvedCandidate]
      for c in vote:
        urn = urn + ([c]*self._numberOfReturned)
      votes[i] = vote
    return candidates, votes

  def description(self):
    return "UrnModel, prob:{}, returned: {}".format(self._approvalProbability, self._numberOfReturned)

  def parameters(self):
    return (self._numberOfReturned, self._approvalProbability)

class PabulibElectionBasedDistribution(VotesGenerator):
  def __init__(self, baseElectionPath):
    self._baseElectionPath = baseElectionPath

  def parameters(self):
    return (None, None)

  def generate(self, candidatesCount, votesCount):
    """Right now candidatesCount is ignored"""
    candidates, allVotes = self._parsePabulibElections()
    #if not candidatesCount == allCandidatesCount:
    #  raise ValueError("Right now one cannot generate pabulib elections"
    #  "with a different number of candidates that they originally have")
    votes = {}
    if len(allVotes) < votesCount:
      raise ValueError(f"Too small elections to draw {votesCount} votes")
    for vote in random.sample(allVotes, votesCount):
      votes[len(votes)] = vote
    return candidates, votes
  def description(self):
    return f"Pabulib based distribution from: {self._baseElectionPath}"

  def _parsePabulibElections(self):
    cand_name_id = {}
    votes = []
    with open(self._baseElectionPath, 'r', newline='', encoding="utf-8") as csvfile:
      reader = csv.reader(csvfile, delimiter=';')
      for row in reader:
        if str(row[0]).strip().lower() in ["meta", "projects", "votes"]:
          section = str(row[0]).strip().lower()
          header = next(reader)
        elif section == "meta":
          pass
        elif section == "projects":
          cand_name_id[row[0]] = len(cand_name_id);
        elif section == "votes":
          vote_index = header.index("vote")
          vote = row[vote_index].strip().split(",") 
          votes.append([cand_name_id[cand] for cand in vote])
    return sorted(cand_name_id.values()), votes
