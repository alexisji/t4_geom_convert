/**
* @file Statistics.cc
*
*
* @brief Statistics class
*
* @author J. Faustin
* @version 1.0
*/

#include "Statistics.hh"
#include "errorCC.hh"
#include "t4storeevent.hh"
#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <iostream>

using namespace std;

Statistics::Statistics()
{
  nbSuccess = 0;
  nbFailure = 0;
  nbIgnored = 0;
  nbOutside = 0;
  nbT4Volumes = 0;
}

void Statistics::incrementSuccess()
{
  ++nbSuccess;
}

void Statistics::incrementFailure()
{
  ++nbFailure;
}

void Statistics::incrementIgnore()
{
  ++nbIgnored;
}

void Statistics::incrementOutside()
{
  ++nbOutside;
}

int Statistics::getTotalPts()
{
  return nbSuccess + nbFailure + nbIgnored + nbOutside;
}

void Statistics::recordCoveredRank(long rank)
{
  coveredRanks.insert(rank);
}

void Statistics::setNbT4Volumes(long nbVolumes)
{
  nbT4Volumes = nbVolumes;
}

void Statistics::recordFailure(vector<double> position, long rank, int pointID, int cellID, int materialID, double dist)
{
  failedPoint failed{{position[0], position[1], position[2]},
                     double(pointID),
                     double(cellID),
                     double(materialID),
                     dist,
                     double(rank)};
  failures.push_back(failed);
}

vector<failedPoint> Statistics::getFailures()
{
  return failures;
}

void Statistics::report()
{
  cout << "\n---------------------------" << endl;
  cout << "Reporting on MCNP/T4 geometry comparison" << endl;
  cout << "-----------------------------" << endl;

  double maxDist = 0.;
  double averageDist = 0.;
  for(auto const &failedPoint: failures) {
    averageDist += failedPoint.dist;
    maxDist = std::max(maxDist, failedPoint.dist);
  }
  averageDist /= failures.size();

  int totalPt = getTotalPts();
  cout << "Number of SAMPLED points : " << totalPt << endl;
  reportOn("SUCCESSFUL", nbSuccess, totalPt);
  reportOn("FAILED    ", nbFailure, totalPt);
  reportOn("IGNORED   ", nbIgnored, totalPt);
  reportOn("OUTSIDE   ", nbOutside, totalPt);
  cout << "Number of COVERED volumes: " << coveredRanks.size() << endl;
  cout << "Number of INPUT   volumes: " << nbT4Volumes << endl;
  cout << "Average distance to surface for FAILED points: " << averageDist << endl;
  cout << "Maximum distance to surface for FAILED points: " << maxDist << endl;
}

void Statistics::reportOn(const string &status, int data, int total)
{
  cout << "Number of " << status << "     : " << data
       << " -> "
       << 100. * float(data) / float(total)
       << "%" << endl;
}

void Statistics::writeOutForVisu(string &fname)
{
  T4_event_storing<failedPoint> t4_store;
  string rawname = getRawFileName(fname);
  string datFile = rawname + ".failedpoints.dat";
  t4_store.initialize(const_cast<char *>(datFile.c_str()),
                      T4_OUTPUT,
                      ASCII,
                      T4_TYPE_DOUBLE, "x",
                      T4_TYPE_DOUBLE, "y",
                      T4_TYPE_DOUBLE, "z",
                      T4_TYPE_DOUBLE, "pointID",
                      T4_TYPE_DOUBLE, "cellID",
                      T4_TYPE_DOUBLE, "materialID",
                      T4_TYPE_DOUBLE, "dist",
                      T4_TYPE_DOUBLE, "rank",
                      T4_NO_TYPE);

  for (int iFail = 0; iFail < nbFailure; iFail++) {
    t4_store.store(&failures[iFail]);
  }
  t4_store.write_header_dx();
  writePointsFile(rawname);
  t4_store.finalize();
}

string Statistics::getRawFileName(string &fname)
{
  size_t lastindex = fname.find_last_of(".");
  string rawname = fname.substr(0, lastindex);
  lastindex = fname.find_last_of("/");
  if(lastindex != std::string::npos) {
    rawname = rawname.substr(lastindex+1, std::string::npos);
  }
  return rawname;
}

void Statistics::writePointsFile(string &rawname)
{
  ofstream fout(rawname + ".points");
  fout << "name " << rawname + ".failedpoints.general\n";
  fout.close();
}
