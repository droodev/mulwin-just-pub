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

def committeApprovalAndCoverage(candidates, voters, committee):
  commSet = set(committee)
  coverageCounter=0
  for voter in voters.values():
    if len(commSet & set(voter))>0:
      coverageCounter = coverageCounter + 1
  approvalCounter = 0
  for cand in committee:
    for voter in voters.values():
      if cand in voter:
        approvalCounter = approvalCounter + 1
  return coverageCounter, approvalCounter

def loadPrefLibPartialOrder(filepath, groupsApproved):
  profile = {}
  multiplicities = {}
  with open(filepath, 'r') as infile:
    counter = 0
    votersnr = None
    candnr = None
    for line in infile:
      counter = counter + 1
      if counter == 1:
        candnr = int(line.strip())
        continue
      if counter > 1 and counter <= candnr + 1:
        continue
      if counter == candnr + 2:
        votersnr = int(line.strip().split(",")[0])
        continue
      lineparts = line.strip().split(",")
      multiplicity = int(lineparts[0])
      groups = {}
      partnr = 1
#      print lineparts
      while partnr <= len(lineparts[1:]):
        part = lineparts[partnr]
        if part == "{}" or part == "":
          groupApproved = []
        elif part.startswith("{"):
          endpartnr = partnr
          while not lineparts[endpartnr].endswith("}"):
            endpartnr = endpartnr + 1
          groupApproved = reduce(lambda acc, elem: acc + [int(elem)-1],
              (",".join(lineparts[partnr:endpartnr+1])[1:-1]).split(","), [])
          partnr = endpartnr
        else:
          groupApproved = [int(part)-1]
        groups[len(groups)] = groupApproved
        partnr = partnr + 1

      approved = reduce(lambda acc, elem: acc + elem, [g for gnr, g in
        groups.items() if gnr<groupsApproved], [])

      nextVoteNr = len(profile)
      profile[nextVoteNr] = approved
      multiplicities[nextVoteNr] = multiplicity
  return profile, range(candnr), multiplicities


class Mesh(object):

  def _computeRanges(self, minVal, maxVal, parts):
    step = maxVal//parts
    lowerBounds = range(minVal, maxVal+1, step)
    ranges = [(lowerBound,lowerBound+step-1) for lowerBound in lowerBounds]
    if ranges[-1][1] != maxVal:
      ranges[-1] = (ranges[-1][0], maxVal)
    return ranges

  def _initializeCells(self):
    coverageRanges = self._computeRanges(1, self._maxCoverage, self.coverageParts)
    approvalRanges = self._computeRanges(1, self._maxApproval, self.approvalParts)
    self._cells = {cR + aR: self._initVal for cR in coverageRanges for aR in approvalRanges}
    self._cellStatus = {cell: True for cell in self._cells}

  def _initializeCellsCoordinates(self):
    """ Starting from 1 (not from 0)"""
    self._cellCoordinate = {}
    colCounter = 0
    rowCounter = self.coverageParts
    for cell in self._sortCells_Fragile(self._cells):
      self._cellCoordinate[cell] = (rowCounter, colCounter + 1)
      colCounter = (colCounter + 1) % self.approvalParts
      if colCounter == 0:
        rowCounter = rowCounter - 1

  def _sortCells_Fragile(self, cells): 
    return sorted(cells, key = lambda cell: (-cell[0], cell[2]))

  def _sortCells(self, cells): 
    return self._sortCells_Fragile(cells)

  def getClippedCells(self):
    return self._sortCells([c for c in self._cells if self._cellStatus[c] is False])

  def getUnclippedCells(self):
    return self._sortCells([c for c in self._cells if self._cellStatus[c] is True])

  def getAllCells(self):
    return self._sortCells(self._cells)

  def setValueOfCell(self, cell, value):
    self._cells[cell] = value

  def getValueOfCell(self, cell, value):
    return self._cells[cell]

  def findAndSetValue(self, coverage, approval, value):
    cell = self.getCellFromValues(coverage, approval)
    self.setValueOfCell(cell, value)

  def getCellFromValues(self, coverage, approval):
    for cell in self._cells.keys():
      cCLB, cCUB, cALB, cAUB = cell
      if cCLB <= coverage and cCUB >= coverage and cALB <= approval and cAUB >= approval:
        return cell

  def getCellCoordinate(self, cell):
    return self._cellCoordinate[cell]

  def clipCell(self, cell):
    self._cellStatus[cell] = False

  def unclipCell(self, cell):
    self._cellStatus[cell] = True

  def clipMesh(self, fromDownC, fromUpC, fromDownA, fromUpA):
    for cell, coordinate in self._cellCoordinate.items():
      covCoor, appCoor = coordinate
      if covCoor <= fromDownC or covCoor + fromUpC > self.coverageParts or \
      appCoor <= fromDownA or appCoor + fromUpA > self.approvalParts:
        self.clipCell(cell)

  def clipMeshByValues(self, minC, maxC, minApp, maxApp):
    for cell in self._cells.keys():
      cCLB, cCUB, cALB, cAUB = cell
      if cCUB < minC or cCLB > maxC or cAUB < minApp or cALB > maxApp:
        self.clipCell(cell)

  def depict(self, outStream):
    columnCounter = 0
    for cell in self.getAllCells():
      outStream.write(str(self._cells[cell]))
      columnCounter = (columnCounter+1) % self.approvalParts
      if columnCounter == 0:
        outStream.write("\n")

  def __init__(self, candidatesNr, votersNr, committeeSize, coverageParts, approvalParts, initVal="."):
    self.candidatesNr = candidatesNr
    self.committeeSize = committeeSize
    self.coverageParts = coverageParts
    self.approvalParts = approvalParts
    self.votersNr = votersNr
    self._initVal = initVal
    self._maxApproval = committeeSize*votersNr
    self._maxCoverage = votersNr
    self._initializeCells()
    self._initializeCellsCoordinates()


