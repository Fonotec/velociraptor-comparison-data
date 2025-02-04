from velociraptor.observations.objects import ObservationalData

import unyt
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import scipy.stats as stats


def bin_data_general(array_x, array_y, array_x_bin):
    array_x_bin_centres = 0.5 * (array_x_bin[1:] + array_x_bin[:-1])
    y_array_bin, _, _ = stats.binned_statistic(
        array_x, array_y, statistic="median", bins=array_x_bin
    )
    y_array_bin_std_up, _, _ = stats.binned_statistic(
        array_x, array_y, statistic=lambda x: np.percentile(x, 84.0), bins=array_x_bin
    )
    y_array_bin_std_down, _, _ = stats.binned_statistic(
        array_x, array_y, statistic=lambda x: np.percentile(x, 16.0), bins=array_x_bin
    )

    y_array_bin_std_up = y_array_bin_std_up - y_array_bin
    y_array_bin_std_down = y_array_bin - y_array_bin_std_down

    return array_x_bin_centres, y_array_bin, y_array_bin_std_down, y_array_bin_std_up


# Exec the master cosmology file passed as first argument
with open(sys.argv[1], "r") as handle:
    exec(handle.read())

for dx in [100, 500, 1000]:
    input_filename = f"../raw/Pessa2021_{dx}pc.dat"

    processed = ObservationalData()

    comment = f"Based on the PHANGS data [{dx} pc]"
    citation = "Pessa et al. (2021)"
    bibcode = "2021A&A...650A.134P"
    name = "Spatially-resolved $\\Sigma_{\\star}$ vs $\\Sigma_{\\rm H_2}$"
    plot_as = "points"

    # Reading the Pessa 2021 data

    array_of_interest = np.arange(-1, 4.75, 0.25)+6.
    minimum_surface_density = 8.0  # in their paper this seems to be the limit they can observe, however they do not say anything about this
    array_of_interest = array_of_interest[array_of_interest >= minimum_surface_density]
    if array_of_interest[0] > minimum_surface_density:
        array_of_interest = np.append([minimum_surface_density], array_of_interest)

    Sigma_star, Sigma_H2 = np.genfromtxt(input_filename, unpack=True)

    Sigma_H2 = 10 ** (Sigma_H2) 

    Sigma_star = ( 10 ** (Sigma_star) )

    binned_data = bin_data_general(
        np.log10(Sigma_star), np.log10(Sigma_H2), array_of_interest
    )

    Sigmastar = unyt.unyt_array(10 ** binned_data[0], units="Msun/kpc**2")

    SigmaH2 = unyt.unyt_array(10 ** binned_data[1], units="Msun/kpc**2")

    SigmaH2_err = unyt.unyt_array(
        [
            np.abs(10 ** (binned_data[1]) - 10 ** (binned_data[1] - binned_data[2])),
            np.abs(10 ** (binned_data[1] + binned_data[3]) - 10 ** (binned_data[1])),
        ],
        units="Msun/kpc**2",
    )

    array_x_bin_std_up = array_of_interest[1:] - binned_data[0]
    array_x_bin_std_down = binned_data[0] - array_of_interest[:-1]

    Sigmastar_err = unyt.unyt_array(
        [
            10 ** (binned_data[0]) - 10 ** (binned_data[0] - array_x_bin_std_down),
            10 ** (binned_data[0] + array_x_bin_std_up) - 10 ** (binned_data[0]),
        ],
        units="Msun/kpc**2",
    )

    processed.associate_x(
        Sigmastar, scatter=Sigmastar_err, comoving=False, description="$\\Sigma_{\\star}$"
    )

    processed.associate_y(
        SigmaH2, scatter=SigmaH2_err, comoving=False, description="$\\Sigma_{\\rm H_2}$"
    )

    processed.associate_citation(citation, bibcode)
    processed.associate_name(name)
    processed.associate_comment(comment)
    processed.associate_redshift(0.0, 0.0, 0.0)
    processed.associate_plot_as(plot_as)
    processed.associate_cosmology(cosmology)

    output_path = f"../Pessa2021_{dx}_pc.hdf5"

    if os.path.exists(output_path):
        os.remove(output_path)

    processed.write(filename=output_path)
