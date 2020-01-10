#include "options_compare.hh"
#include "help.hh"
#include <cstdio>
#include <cstdlib>
#include <unistd.h>

using namespace std;

/** \brief Display the command line help
 */
void help()
{
  std::cout << endl
            << "oracle\n"
            << "\n  Compare MCNP and T4 geometries check that they are weakly equivalent."
            << "\n  A point is assumed to match by checking the name of the composition at"
            << "\n  that point in each geometry."
            << "\n\nUSAGE"
            << "\n\toracle [options] jdd.t4 jdd.inp ptrac" << endl
            << endl;

  std::cout << "INPUT FILES" << endl;
  edit_help_option("jdd.t4", "A TRIPOLI-4 input file converted from MCNP INP file.");
  edit_help_option("jdd.inp", "The MCNP INP file that was used for the conversion.");
  edit_help_option("ptrac", "The MCNP PTRAC file corresponding to the INP file.");

  std::cout << endl
            << "OPTIONS" << endl;
  edit_help_option("-V, --verbose", "Increase output verbosity.");
  edit_help_option("-h, --help", "Displays this help message.");
  edit_help_option("-n, --npts", "Maximum number of tested points.");
  edit_help_option("-d, --delta", "Distance to the nearest surface below which a failed test is ignored.");
  edit_help_option("-g, --guess-material-assocs", "guess the materials correspondence based on the first few points");
  edit_help_option("--binary,---ascii", "Specify the format of the MCNP PTRAC file");

  std::cout << endl;
}

/** \brief Constructor of the class
*/
OptionsCompare::OptionsCompare() : help(false),
                                   verbosity(0),
                                   delta(1.0E-7),
                                   guessMaterialAssocs(false),
                                   ptracFormat(PTRACFormat::BINARY)
{
}

/** \brief Get the options set in the command line
 * @param[in] argc The number of arguments in the command line
 * @param[in] argv The splitted command line
 */
void OptionsCompare::get_opts(int argc, char **argv)
{

  if (argc <= 3) {
    help = true;
    return;
  } else {

    for (int i = 1; i < argc; i++) {
      string opt(argv[i]);

      if (opt == "--help" || opt == "-h") {
        help = true;
        return;
      } else if (opt == "--verbose" || opt == "-V") {
        ++verbosity;
      } else if (opt == "--guess-material-assocs" || opt == "-g") {
        guessMaterialAssocs = true;
      } else if (opt == "--npts" || opt == "-n") {
        int nv = 1;
        check_argv(argc, i + nv);
        long const npoints_arg = int_of_string(argv[i + 1]);
        if(npoints_arg <= 0) {
          std::cout << "Warning: npoints<=0. Ignored." << std::endl;
        } else {
          npoints = std::make_unique<long>(npoints_arg);
        }
        i += nv;
      } else if (opt == "--delta" || opt == "-d") {
        int nv = 1;
        check_argv(argc, i + nv);
        istringstream os(argv[i + 1]);
        os >> delta;
        if (delta <= 0) {
          std::cout << "Warning: delta<=0. Setting delta=1.0e-7" << std::endl;
          delta = 1.0e-7;
        }
        i += nv;
      } else if (opt == "--binary") {
        ptracFormat = PTRACFormat::BINARY;
      } else if (opt == "--ascii") {
        ptracFormat = PTRACFormat::ASCII;
      } else {
        filenames.push_back(opt);
      }
    }
  }

  // check that all the input files exist
  for (vector<string>::const_iterator fname = filenames.begin(), efname = filenames.end();
       fname != efname; ++fname) {
    if (access(fname->c_str(), R_OK) == -1) {
      cout << "'" << *fname << "': unknown option or unreachable file." << endl;
      cout << "Try '" << argv[0] << " --help for more information.\n"
           << endl;
      exit(EXIT_FAILURE);
    }
  }
}

/** \brief Check if the position of the last value for an option is compatible
 * with the line command line.
 * \param argc The number of arguments in the line command.
 * \param ip   The expected position of the last value of the option in the
 * commmand line.
 */
void OptionsCompare::check_argv(int argc, int ip)
{
  if (ip >= argc) {
    cout << "\nError in command line.\n"
         << endl;
    exit(EXIT_FAILURE);
  }
}
