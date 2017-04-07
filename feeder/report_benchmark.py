
from optparse import OptionParser
import csv
import numpy as np
from collections import defaultdict


def create_report(input_file, csvout_file):
    with open(input_file) as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [r for r in reader]

    by_clients_for_img = defaultdict(list)
    by_clients_for_h264 = defaultdict(list)
    by_clients = {
        'img': by_clients_for_img,
        'h264': by_clients_for_h264
    }

    csvout = open(csvout_file, "w")
    csvout.write("clients,format,cpu_avg,cpu_std,mem_used_avg,mem_used_std,fps_avg,fps_std\n")

    for row in rows:
        clients_num = row['clients']
        format = row['format']
        if format == "img":
            by_clients_for_img[clients_num].append(row)
        else:
            by_clients_for_h264[clients_num].append(row)

    # Now calculate the averages
    for clients_num, rows in sorted(by_clients_for_img.items(), key=lambda item: int(item[0])):
        assert type(rows) == list

        results = {}
        for var in ['cpu', 'mem_used', 'fps']:
            var_list = list(map(lambda r: float(r[var]), rows))
            avg = np.average(var_list)
            std = np.std(var_list, ddof=1)
            results[var] = {'avg': avg, 'std': std}

        csvrep = "{},{},{},{},{},{},{},{}".format(clients_num, 'img', results['cpu']['avg'], results['cpu']['std'],
                                               results['mem_used']['avg'], results['mem_used']['std'],
                                               results['fps']['avg'], results['fps']['std'])

        print(csvrep)
        csvout.write(csvrep + "\n")



    print("{}".format(rows))


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", metavar="FILE", default="csvexample.txt", dest="input", help="Path to the benchmark input file")
    parser.add_option("-c", "--csvoutput", metavar="FILE", default="out.csv", dest="csvoutput", help="Path to the CSV output file")

    (options, args) = parser.parse_args()

    create_report(options.input, options.csvoutput)