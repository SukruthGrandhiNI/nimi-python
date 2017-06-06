#!/usr/bin/python

from mako.template import Template
from mako.exceptions import RichTraceback
import logging
import argparse
import sys, os

import pprint
pp = pprint.PrettyPrinter(indent=3)

types = {
    'ViStatus': 'c_long',
    'ViRsrc': 'c_char_p',
    'ViBoolean': 'c_ushort',
    'ViSession': 'c_ulong',
    'ViChar': 'c_char_p',
    'ViUInt32': 'c_ulong',
    'ViInt32': 'c_long',
    'ViInt16': 'c_short',
    'ViUInt16': 'c_ushort',
    'ViReal32': 'c_float',
    'ViReal64': 'c_double',
    'ViString': 'c_char_p',
    'ViConstString': 'c_char_p',
    'ViAttr': 'c_long',
}

def configureLogging(lvl = logging.WARNING, logfile = None):
    root = logging.getLogger()
    root.setLevel(lvl)
    formatter = logging.Formatter('%(funcName)s - %(levelname)s - %(message)s')
    if logfile is None:
        hndlr = logging.StreamHandler(sys.stdout)
    else:
        print("Logging to file %s" % logfile)
        hndlr = logging.FileHandler(logfile)
    hndlr.setFormatter(formatter)
    root.addHandler(hndlr)

def main():
    # Setup the required arguments for this script
    usage = "usage: " + sys.argv[0] + " [options]"

    parser = argparse.ArgumentParser(description=usage)
    fileGroup = parser.add_argument_group("Input and Output files")
    fileGroup.add_argument(
        "--template",
        action="store", dest="template", default=None, required=True,
        help="Mako template to use")
    fileGroup.add_argument(
        "--dest-file",
        action="store", dest="dest", default=None, required=True,
        help="Output file")
    fileGroup.add_argument(
        "--driver",
        action="store", dest="driver", default=None, required=True,
        help="Driver folder name")

    verbosityGroup = parser.add_argument_group("Verbosity, Logging & Debugging")
    verbosityGroup.add_argument(
        "-v", "--verbose",
        action="count", dest="verbose", default=0,
        help="Verbose output"
        )
    verbosityGroup.add_argument(
        "--test",
        action="store_true", dest="test", default=False,
        help="Run doctests and quit"
        )
    verbosityGroup.add_argument(
        "--log-file",
        action="store", dest="logfile", default=None,
        help="Send logging to listed file instead of stdout"
        )
    args = parser.parse_args()

    if args.verbose > 1:
        configureLogging(logging.DEBUG, args.logfile)
    elif args.verbose == 1:
        configureLogging(logging.INFO, args.logfile)
    else:
        configureLogging(logging.WARNING, args.logfile)

    logging.info(pp.pformat(args))

    sys.path.append(os.path.normpath(os.path.join(sys.path[0], '..', args.driver, 'metadata')))

    try:
        import functions
        import config
        import attributes
        import enums
    except ImportError as e:
        logging.error("Error importing metadata")
        logging.error(e)
        sys.exit(1)

    logging.debug(pp.pformat(functions))

    template = Template(filename=args.template)
    templateParams = {}
    templateParams['functions'] = functions.functions
    templateParams['attributes'] = attributes.attributes
    templateParams['config'] = config.config
    templateParams['enums'] = enums.enums
    templateParams['types'] = types

    logging.debug(pp.pformat(templateParams))

    try:
        renderedTemplate = template.render(templateParameters=templateParams)

    except:
        # Because mako expands into python, we catch all errors, not just MakoException.
        # Ideally, we'd use text_error_template, but it sucks.  html_error_template,
        # however, is useful.  Unfortunately emitting html isn't acceptable.  So we
        # re-implement using mako.exceptions.RichTraceback here.
        tback = RichTraceback(traceback=None)
        line = tback.lineno
        lines = tback.source.split('\n')

        # The underlying error.
        logging.error("\n%s: %s\n" % ( str(tback.error.__class__.__name__), str(tback.error) ))
        logging.error("Offending Template: %s\n" % args.template)

        # Show a source listing of the template, with offending line marked.
        for index in range(max(0, line - 4), min(len(lines), line + 5)):
            if index + 1 == line:
                logging.error(">> %#08d: %s" % (index + 1, lines[index]))
            else:
                logging.error("   %08d: %s" % (index + 1, lines[index]))

        logging.error("\nTraceback (most recent call last):")
        for (filename, lineno, function, line) in tback.reverse_traceback:
            logging.error("   File %s, line %d, in %s\n     %s" % (filename, lineno, function, line))

        logging.error("\n")
        sys.exit(1)

    print(renderedTemplate)
    fileHandlePublic = open(args.dest, 'w')
    fileHandlePublic.write(renderedTemplate)
    fileHandlePublic.close()


if __name__ == '__main__':
    main()

