
from optparse import OptionParser
import csv
import numpy as np
from collections import defaultdict


def create_report(input_file, browser_input_file, csvout_file, format_option):

    print("FORMAT chosen is: {}".format(format_option))

    with open(input_file) as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [r for r in reader]

    with open(browser_input_file) as browser_csvfile:
        reader = csv.DictReader(browser_csvfile)
        browser_rows = [r for r in reader if not r['clients'].startswith('clients')]  # Ignore the repeated headers.

    by_clients_for_img = defaultdict(list)
    by_clients_for_h264 = defaultdict(list)
    by_clients = {
        'img': by_clients_for_img,
        'h264': by_clients_for_h264
    }

    browser_by_clients_for_img = defaultdict(list)
    browser_by_clients_for_h264 = defaultdict(list)
    browser_by_clients = {
        'img': browser_by_clients_for_img,
        'h264': browser_by_clients_for_h264
    }

    csvout = open(csvout_file, "w")
    csvout.write("clients,format,cpu_avg,cpu_std,mem_used_avg,mem_used_std,bw_avg,bw_std,fps_avg,fps_std,lat_avg,lat_std,n\n")

    # Organize the standard results log according to their format.
    for row in rows:
        clients_num = row['clients']
        format = row['format']
        if format == "img":
            by_clients_for_img[clients_num].append(row)
        else:
            by_clients_for_h264[clients_num].append(row)

    # Organize the browser results log according to their format.
    for brow in browser_rows:
        clients_num = brow['clients']
        format = brow['format']
        if format == "img":
            browser_by_clients_for_img[clients_num].append(brow)
        else:
            browser_by_clients_for_h264[clients_num].append(brow)


    clients_number = min(len(by_clients_for_img), len(by_clients_for_h264), len(browser_by_clients_for_h264), len(browser_by_clients_for_img))
    print("Clients number: {}".format(clients_number))

    results_by_clients = {
        'img': defaultdict(dict),
        'h264': defaultdict(dict)
    }



    # Now calculate the averages, for the standard rows. FPS and lat is not registered here, it is in the browser-results log.
    for clients_num, rows in sorted(by_clients_for_img.items(), key=lambda item: int(item[0])):
        assert type(rows) == list

        results = results_by_clients[format_option][clients_num]
        for var in ['cpu', 'mem_used', 'bw']:
            try:
                var_list = list(map(lambda r: float(r[var]), rows))
                avg = np.average(var_list)
                std = np.std(var_list, ddof=1)
                results[var] = {'avg': avg, 'std': std}
            except:
                print("Could not process var: {}".format(var))

    # Now calculate the averages, for the FPS and LAT, which are in the browser-results log.
    for clients_num, browser_rows in sorted(browser_by_clients_for_img.items(), key=lambda item: int(item[0])):
        assert type(browser_rows) == list

        results = results_by_clients[format_option][clients_num]
        for var in ['fps', 'lat']:
            try:
                var_list = list(map(lambda r: float(r[var]), browser_rows))
                avg = np.average(var_list)
                std = np.std(var_list, ddof=1)
                results[var] = {'avg': avg, 'std': std, 'n': len(var_list)}
            except:
                print("Could not process var: {}".format(var))


    for clients_num in range(1, clients_number+1):
        results = results_by_clients[format_option]["{}".format(clients_num)]

        print("{}".format(results))

        csvrep = "{},{},{},{},{},{},{},{},{},{},{},{},{}".format(clients_num, format_option, results['cpu']['avg'], results['cpu']['std'],
                                               results['mem_used']['avg'], results['mem_used']['std'],
                                               results['bw']['avg'], results['bw']['std'], results['fps']['avg'], results['fps']['std'],
                                               results['lat']['avg'], results['lat']['std'], results['lat']['n'])
        print(csvrep)
        csvout.write(csvrep + "\n")


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", metavar="FILE", default="csvexample.txt", dest="input", help="Path to the standard server benchmark input file")
    parser.add_option("-b", "--browserinput", metavar="FILE", default="testresults.txt", dest="browserinput", help="Path to the browser results input file")
    parser.add_option("-c", "--csvoutput", metavar="FILE", default="out.csv", dest="csvoutput", help="Path to the CSV output file")
    parser.add_option("-f", "--format", default="img", type="string", dest="format", help="Format to take into account")

    (options, args) = parser.parse_args()

    create_report(options.input, options.browserinput, options.csvoutput, options.format)