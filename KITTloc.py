import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
# import scipy
from scipy.fft import fft, ifft
from scipy.signal import find_peaks  # , convolve, unit_impulse

# from refsignal import refsignal
from wavaudioread import wavaudioread

from scipy.optimize import least_squares
# from recording_tool import recording_tool

# The class localization contains all relevant functions, including signal preparation, signal processing,
# location estimation signal processing, location estimationerror estimation, and plotting.
class Localization:

    # runs when the localization class is used
    def __init__(self, debug=False, y_ref=np.array([]), repeat_count=1, skipcount = 10000):

        self.mics_xpos = [0, 0, 460, 460, 0]
        self.mics_ypos = [0, 460, 460, 0, 230]
        self.mics_zpos = [50, 50, 50, 50, 80]

        self.beacon_height = 24.8

        self.Fs = 44100
        self.epsi = 0.05

        self.filename = None
        self.full_signal_m1 = None
        self.intervals = None
        self.time_diffs = None
        self.y = None

        self.begin, self.end = 0, 0
        self.debug = debug
        self.real_x = 0
        self.real_y = 0
        self.index = 0

        self.y_ref = y_ref
        self.repeat_count = repeat_count
        self.skipcount = skipcount

        self.peak_error = 0

    # prepare_signal takes in a filename and extracts the microphone signals from it, it also extracts the reference
    # signal the signals are then truncated based to extract a single peak the function outputs the truncated
    # reference signal (y_ref), the truncated microphone signals (y), the full microphone 1 recording (
    # full_signal_m1) the sample value where the truncated signals start (begin), and the sample value where the
    # truncated signals end (end)
    def prepare_ref(self, name):
        y_ref = np.array(wavaudioread("10-jun-test-ref.wav", self.Fs))
        skipcount = 20000

        index = self.findpeak(y_ref.T[0][skipcount:], 0, 0.8, 100)
        begin = skipcount - 250 + index  # begin slightly before the peak that was found
        end = skipcount + 1500 + index

        new_ref = y_ref[begin:end, :5]

        print(f'ref len before save: %d' %len(new_ref.T[0]))

        wavfile.write( name , self.Fs, new_ref)
        t = np.arange(len(new_ref.T[0]))

        plt.plot(t, new_ref.T[0])
        plt.xlabel(r"Sample")
        plt.ylabel("Amplitude")
        plt.title("Reference")
        plt.show()

    def prepare_signal(self, current_peak):

        # find the first peak using the first microphone signal, after skipping -skipcount -samples

        index = self.findpeak(self.recording.T[0][self.skipcount:], current_peak, 0.5, 1000)

        self.index = index

        begin = index + self.skipcount - 2000  # begin slightly before the peak that was found
        end = index + self.skipcount + 3000

        if self.debug:
            print("\n-- prepare function debug info:")
            print(f'peak isolated at sample: %d' % (index + self.skipcount))
            self.full_signal_m1 = self.recording

        self.y = self.recording[begin:end, :5]  # replace the originals with cut versions

        return

    def merge_recordings(self, fileroot, amount):

        y_ref = np.array(wavaudioread("test_ref.wav", 44100))

        for i in range(amount):
            name = fileroot + '-' + str(i) #recordings should be of the format fileroot-1, fileroot-2, ect.
            if i == 0:
                y = np.array(wavaudioread(name, 44100))
            else:
                y += name

        return y

    # findpeak takes in a signal (x) and returns the sample value of the n-th peak, specified by an interger "index"
    # the value ratio determines what fraction of maximum absolute signal value counts as a peak
    # minimum distance prevents peaks that happen in quick succession from being detected as seperate peaks.
    def findpeak(self, x, index, ratio, minimum_distance):

        try:
            treshold = ratio * max(x)
            peaks = find_peaks(x, height=treshold, distance=minimum_distance)  # finds all of the peaks in the signal
            peak = peaks[0][index]  # selects the n-th item in the peaks list where n is the index variable
        except:
            self.error_flag = 1
            print("error in findpeak, setting peak index to 1000!")
            peak = 1000

        return peak

    # ch3 is our channel estimation function, it makes use of frequency domain deconvolution to obtain the channel
    # estimate ch3 takes in x, the recorded signal, y, the reference signal, and epsi, used to set small values to
    # some minimum, which avoids noise problems it returns the channel estimate (h)
    def ch3(self, x, y, epsi):
        Nx = len(x)  # Length of x
        Ny = len(y)  # Length of y
        Nh = Ny - Nx + 1  # Length of h

        # Force x to be the same length as y
        x = np.append(x, [0] * (Nh - 1))

        # Deconvolution in frequency domain
        Y = fft(y)
        X = fft(x)
        H = Y / X

        # Threshold to avoid blow ups of noise during inversion
        ii = np.absolute(X) < epsi * max(np.absolute(X))
        H[ii] = 0

        h = np.real(ifft(H))  # ensure the result is real
        # h = h[0:Nh]              # optional: truncate to length Lhat (L is not reliable?)
        return h

    # the not so aptly named TDOA2 does not calculate TDOA's, instead, it calculates TOA's. TDOA2 takes in a recorded
    # signal y and a reference signal y_ref, it internally runs the ch3 function to obtain a channel estimate TDOA2
    # then runs the findpeak function to detect at which sample the large delta like peak is located, this sample
    # values indicates the time difference between the reference and recording, it returns this time interval,
    # which is the TOA.
    def TOA(self, y_ref, y):

        y = np.concatenate((y, np.zeros(1000)))
        # use ch3 to estimate channel
        h = self.ch3(y_ref, y, self.epsi)

        peak_sample = self.findpeak(h, 0, 1, 30)

        # print(peak_sample)
        # take the first peak's index and calculate microphone distance
        time_interval = peak_sample / self.Fs  # gets the time interval between zero and the big channel estimate peak

        return (time_interval)

    # distances simply runs TDOA2 for each microphone signal in a given recording and outputs a list of TOA's (
    # intervals), do not mind its name. distances takes in a recorded signal y and a reference signal y_ref to pass
    # to TDOA2
    def get_intervals(self):
        intervals = []

        if self.debug:
            print("\n-- distances function debug info:")

        for i in range(5):
            ref = self.y_ref[:, 0]
            rec = self.y[:, i]
            time_interval = self.TOA(ref, rec)

            intervals += [time_interval]
            if self.debug:
                print("Estimated TOA for mic %d: %.6f sec" % (i + 1, time_interval))

        return intervals

    # pairs takes in a list of TOA's (intervals) and calculates a list of TDOA's (time_diffs) by looping trough each
    # microphone pair
    def get_TDOAS(self):
        mic_pairs = [[1, 2], [1, 3], [1, 4], [1, 5], [2, 3], [2, 4], [2, 5], [3, 4], [3, 5], [4, 5]]
        time_diffs = []

        if self.debug:
            print("\n-- pairs function debug info:")

        for i in range(len(mic_pairs)):
            TOA1 = self.intervals[mic_pairs[i][0] - 1]
            TOA2 = self.intervals[mic_pairs[i][1] - 1]
            time_diffs += [TOA1 - TOA2]
            if self.debug:
                print(f'Time diff D%d%d: %f - %f = %f sec' % (
                    mic_pairs[i][0], mic_pairs[i][1], TOA1, TOA2, time_diffs[i]))
        return time_diffs

    # localisation takes in a list of TDOA's (time diffs) and uses linear algebra to estimate the location of the
    # car, based on a least squares approach localisation outputs the estimated car coordinates
    import numpy as np
    from scipy.optimize import minimize

    def estimate_location(self):

        mic_positions = np.array([[self.mics_xpos], [self.mics_ypos], [self.mics_zpos]]).T

        initial_guess = 230, 230 # take middle of field as initial guess

        sound_speed = 34300  # in cm / sec
        dist_diffs = np.array(self.time_diffs) * sound_speed  # Distance differences in cm

        def residuals(car_coords):
            car_x, car_y = car_coords
            car_position = np.array([car_x, car_y, self.beacon_height])
            theoretical_diffs = []

            # Calculate theoretical distance differences
            for i in range(len(mic_positions)):
                for j in range(i + 1, len(mic_positions)):
                    d_i = np.linalg.norm(car_position - mic_positions[i])
                    d_j = np.linalg.norm(car_position - mic_positions[j])
                    theoretical_diffs.append(d_i - d_j)

            theoretical_diffs = np.array(theoretical_diffs)
            return theoretical_diffs - dist_diffs

        # Perform least squares optimization to minimize the residuals
        result = least_squares(residuals, initial_guess, method='lm')

        # Extract the estimated (x, y) coordinates of the car
        estimated_x, estimated_y = result.x

        return estimated_x, estimated_y  # Return the estimated x and y coordinates

    def estimate_location_old(self):
        mx = self.mics_xpos
        my = self.mics_ypos

        sound_speed = 34300  # in cm / sec
        dist_diffs = np.multiply(self.time_diffs, sound_speed)

        X = np.array([my, mx]).T

        A = np.array([[2 * (mx[1] - mx[0]), 2 * (my[1] - my[0]), -2 * dist_diffs[0], 0, 0, 0],
                      [2 * (mx[2] - mx[0]), 2 * (my[2] - my[0]), 0, -2 * dist_diffs[1], 0, 0],
                      [2 * (mx[3] - mx[0]), 2 * (my[3] - my[0]), 0, 0, -2 * dist_diffs[2], 0],
                      [2 * (mx[4] - mx[0]), 2 * (my[4] - my[0]), 0, 0, 0, -2 * dist_diffs[3]],
                      [2 * (mx[2] - mx[1]), 2 * (my[2] - my[1]), 0, -2 * dist_diffs[4], 0, 0],
                      [2 * (mx[3] - mx[1]), 2 * (my[3] - my[1]), 0, 0, -2 * dist_diffs[5], 0],
                      [2 * (mx[4] - mx[1]), 2 * (my[4] - my[1]), 0, 0, 0, -2 * dist_diffs[6]],
                      [2 * (mx[3] - mx[2]), 2 * (my[3] - my[2]), 0, 0, -2 * dist_diffs[7], 0],
                      [2 * (mx[4] - mx[2]), 2 * (my[4] - my[2]), 0, 0, 0, -2 * dist_diffs[8]],
                      [2 * (mx[4] - mx[3]), 2 * (my[4] - my[3]), 0, 0, 0, -2 * dist_diffs[9]]])

        b = np.array([[dist_diffs[0] ** 2 - np.linalg.norm(X[0]) ** 2 + np.linalg.norm(X[1]) ** 2],  # 12
                      [dist_diffs[1] ** 2 - np.linalg.norm(X[0]) ** 2 + np.linalg.norm(X[2]) ** 2],  # 13
                      [dist_diffs[2] ** 2 - np.linalg.norm(X[0]) ** 2 + np.linalg.norm(X[3]) ** 2],  # 14
                      [dist_diffs[3] ** 2 - np.linalg.norm(X[0]) ** 2 + np.linalg.norm(X[4]) ** 2],  # 15
                      [dist_diffs[4] ** 2 - np.linalg.norm(X[1]) ** 2 + np.linalg.norm(X[2]) ** 2],  # 23
                      [dist_diffs[5] ** 2 - np.linalg.norm(X[1]) ** 2 + np.linalg.norm(X[3]) ** 2],  # 24
                      [dist_diffs[6] ** 2 - np.linalg.norm(X[1]) ** 2 + np.linalg.norm(X[4]) ** 2],  # 25
                      [dist_diffs[7] ** 2 - np.linalg.norm(X[2]) ** 2 + np.linalg.norm(X[3]) ** 2],  # 34
                      [dist_diffs[8] ** 2 - np.linalg.norm(X[2]) ** 2 + np.linalg.norm(X[4]) ** 2],  # 35
                      [dist_diffs[9] ** 2 - np.linalg.norm(X[3]) ** 2 + np.linalg.norm(X[4]) ** 2]])  # 45

        y = np.matmul(np.linalg.inv(np.matmul(A.T, A)), np.matmul(A.T, b))  # solve the matrix
        estimated_x = y[0][0]
        estimated_y = y[1][0]

        return estimated_x, estimated_y

    # locate runs all the nedded functions to generate a location estimate from an audio file it is mainly used to
    # pass values between the other functions it returns a large amount of values in order to expose them to main.
    # the values are used for debugging and plotting within main.
    def locate(self, y, real_x, real_y):  # this handles the entrity of the localization when called

        estimation_list_x = []
        estimation_list_y = []

        #self.filename = filename
        self.recording = y

        for i in range(self.repeat_count):

            self.real_x = real_x
            self.real_y = real_y

            self.prepare_signal(i)

            #print(f'index: %d' %self.index)

            self.intervals = self.get_intervals()
            self.time_diffs = self.get_TDOAS()
            estimated_x, estimated_y = self.estimate_location()
            #onderstaande hoort eigenlijk onder debug maar voorlopig altijd handig om te tonen
            #self.visualpos(estimated_x, estimated_y)

            if ((estimated_x <= 480) and (estimated_x > 0)):
                estimation_list_x += [estimated_x]
            if ((estimated_y <= 480) and (estimated_y > 0)):
                estimation_list_y += [estimated_y]

            if self.debug:

                self.showcut()
                self.showsigs()
                self.showplots()
                self.estimate_error(estimated_x, estimated_y)
                self.visualpos(estimated_x, estimated_y)

        average_x = np.average(estimation_list_x)
        average_y = np.average(estimation_list_y)
        self.estimate_error(average_x, average_y)

        #print(f'\naverage (x,y): (%.2f, %.2f)' % (average_x, average_y))
        self.index = -1
        #self.visualpos(average_x, average_y)

        return average_x, average_y

    # showcut is used to plot a comparison between the full microphone 1 signal, and the truncated microphone 1
    # signal. it takes in both of the aforementioned signals (y, full_signal_m1) as well as the begin and end value
    # for use in the plot axes real_x and real_y contain the coordinates of the known car location, and are used in
    # the plot title. the function can also show a comparison between the reference signal and the microphone 1
    # signal, used once for reporting but kept nonetheless. the funtion returns nothing
    def showcut(self):

        fig, ax = plt.subplots(10, 1, figsize=(12, 24))

        for i in range(5):

            ft = np.arange(len(self.full_signal_m1[:, i]))
            t = np.arange(len(self.y[:, i]))

            ax[2*i+1].plot(t, self.y[:, i])
            ax[2*i+1].set_title(
                'Cut microphone signal for KITT position (x,y) = (' + str(self.real_x) + ',' + str(self.real_y) + ')')
            ax[2*i+1].set_xlabel("Sample [n]")
            ax[2*i+1].set_ylabel("Magnitude")
            ax[2*i+1].set_xlim(0, len(self.y[:, i]))

            ax[2*i].plot(ft, self.full_signal_m1[:, i])
            ax[2*i].set_title(
                'Full microphone signal for KITT position (x,y) = (' + str(self.real_x) + ',' + str(self.real_y) + ')')
            ax[2*i].set_xlabel("Sample [n]")
            ax[2*i].set_ylabel("Magnitude")
            ax[2*i].set_xlim(0, len(self.full_signal_m1[:, i]))
            ax[2*i].vlines([self.begin, self.end], min(self.full_signal_m1[:, i]), max(self.full_signal_m1[:, i]), colors='black',
                         linestyles='dashed', linewidth=2)

        fig.tight_layout()
        #plt.savefig('signal' + str(self.real_x) + '-' + str(self.real_y) + '.jpeg', dpi=600)
        plt.show()

            # return

            #t = np.arange(len(self.y[:, 0]))
            #fig, ax = plt.subplots(2, 1, figsize=(12, 6))

            #ax[1].plot(t, self.y[:, 2])
            #ax[1].set_title("Recorded microphone signal")
            #ax[1].set_xlabel("Sample [n]")
            #ax[1].set_ylabel("Magnitude")
            #ax[1].set_xlim(0, len(self.y_ref[:, 0]))

            #ax[0].plot(t, self.y_ref[:, 0])
            #ax[0].set_title("Reference signal")
            #ax[0].set_xlabel("Sample [n]")
            #ax[0].set_ylabel("Magnitude")
            #ax[0].set_xlim(0, len(self.y_ref[:, 0]))

            #fig.tight_layout()
            #plt.show()

    # showsigs is similar to the latter half of showcuts but shows the reference and signal comparison for each
    # microphone instead. it was used mainly in earlier stages to investigate what the references and signals look
    # like the function generates a large plot and returns nothing
    def showsigs(self):  # Shows the (cut) signals

        fig, ax = plt.subplots(5, 2, figsize=(10, 20))

        for i in range(5):
            t = np.arange(len(self.y[:, i]))
            tr = np.arange(len(self.y_ref[:, i]))

            ax[i, 1].plot(t, self.y[:, i])
            ax[i, 1].set_title("y of channel %d" % i)
            ax[i, 1].set_xlabel("Sample [n]")
            ax[i, 1].set_ylabel("Magnitude")
            ax[i, 1].set_xlim(0, len(self.y[:, i]))

            ax[i, 0].plot(tr, self.y_ref[:, i])
            ax[i, 0].set_title("y_ref of channel %d" % i)
            ax[i, 0].set_xlabel("Time [s]")
            ax[i, 0].set_ylabel("Magnitude")
            ax[i, 0].set_xlim(0, len(self.y_ref[:, i]))

        fig.tight_layout()
        plt.show()

    # the aptly named showplots shows some more plots. Namely the channel impulse response and channel estimation.
    def showplots(self):  # plot impulse response and channel estimate for each microphone

        text = ['First', 'Second', 'Third', 'Fourth', 'Fifth']  # text for use in plots

        fig, ax = plt.subplots(5, 2, figsize=(10, 10))
        for i in range(5):
            hhat_m = self.ch3(self.y_ref[:, 0], self.y[:, i], self.epsi)
            tm = np.arange(0, len(self.y[:, i]), 1)
            t_em = np.arange(0, len(hhat_m), 1)

            ax[i, 0].plot(tm, self.y[:, i])
            ax[i, 0].set_title(f'%s microphone channel impulse response' % text[i])
            ax[i, 0].set_xlabel("Sample [n]")
            ax[i, 0].set_ylabel("Magnitude")
            ax[i, 0].set_xlim(0, len(self.y[:, i]))

            ax[i, 1].plot(t_em, hhat_m)
            ax[i, 1].set_title(f'%s microphone channel estimation' % text[i])
            ax[i, 1].set_xlabel("Time [s]")
            ax[i, 1].set_ylabel("Magnitude")
            ax[i, 1].set_xlim(0, len(hhat_m))

        fig.tight_layout()
        plt.show()

    # visualpos generates a plot what represent the field, and places markers where the microphones, field edges,
    # estimated car position, and real car position are. it takes in the self explanatory values real_x, real_y,
    # calculated_x, calculated_y
    def visualpos(self, estimated_x, estimated_y):

        markers = ['D', 'D', 'D', 'D', 's']  # used for the shape of mic icons

        plt.figure(figsize=(5, 5))
        plt.title('Visualisation of the field for (x,y) = (' + str(self.real_x) + ',' + str(self.real_y) + ') at index ' + str(self.index), pad=15,
                  fontsize=10)
        plt.grid(True)
        plt.xlim(-20, 480)
        plt.ylim(-20, 480)
        plt.vlines([-10, 470], -10, 470, colors='black', linewidth=2)
        plt.hlines([-10, 470], -10, 470, colors='black', linewidth=2)

        plt.vlines([0, 460], -0, 460, colors='black', linestyles='dashed', linewidth=1)
        plt.hlines([0, 460], 0, 460, colors='black', linestyles='dashed', linewidth=1)

        for i in range(5):
            plt.plot(self.mics_xpos[i], self.mics_ypos[i], marker=markers[i], markersize=20, color='b')
            plt.text(self.mics_xpos[i], self.mics_ypos[i], str(i + 1), color='white', fontsize=16, ha='center',
                     va='center_baseline')
        if self.real_x > -1:
            plt.plot(self.real_x, self.real_y, marker='X', markersize=15, color='r', label='known position')
        plt.plot(estimated_x, estimated_y, marker='*', markersize=15, color='g', label='estimated position')
        plt.legend(handlelength=0.7)
        # plt.savefig(str(real_x) + '-' + str(real_y) + '.jpeg', dpi=600) #used for reporting
        plt.show()

    # estimate error is a large function that calculates and prints useful data for debugging, such as: real TDOA
    # versus eastimated TDOA information, real car location versus estimated car location and the difference between
    # them. real_x and real_y represent the known car location, calculated_x and calculated_y represent the estimated
    # car location, time diffs holds the TDOA value for all microphone pairs
    def estimate_error(self, calculated_x, calculated_y):
        mic_pairs = [[1, 2], [1, 3], [1, 4], [1, 5], [2, 3], [2, 4], [2, 5], [3, 4], [3, 5], [4, 5]]
        travel_time = []
        real_diffs = []

        if self.real_x < -1:
            print("\nerror function will not run since real location is set as unknown")
            return

        print("\n-- error function info:")

        for i in range(5):
            mic_x = self.mics_xpos[i]
            mic_y = self.mics_ypos[i]
            dx = self.real_x - mic_x
            dy = self.real_y - mic_y
            distance = np.sqrt(dx ** 2 + dy ** 2)  # pythagoras
            travel_time += [distance / 34300]

        for i in range(10):
            TOA1 = travel_time[mic_pairs[i][0] - 1]
            TOA2 = travel_time[mic_pairs[i][1] - 1]
            real_diffs += [TOA1 - TOA2]

        #for i in range(10):

        #    if real_diffs[i] == 0:
        #        real_diffs[i] = 0.0000001

        #    error = abs(self.time_diffs[i] - real_diffs[i])
        #    err_percent = error * 100 / abs(real_diffs[i])
        #    print(f'D%d%d: estimated TDOA: %.6f s, real TDOA: %.6f s, error percentage: %.3f%%' % (
        #        mic_pairs[i][0], mic_pairs[i][1], self.time_diffs[i], real_diffs[i], err_percent))

        x_error = abs(calculated_x - self.real_x)
        x_error_percent = x_error * 100 / 480
        y_error = abs(calculated_y - self.real_y)
        y_error_percent = y_error * 100 / 480

        error_dist = np.sqrt((self.real_x - calculated_x) ** 2 + (self.real_y - calculated_y) ** 2)

        print(f'real (x,y): %.2f cm, %.2f cm' % (self.real_x, self.real_y))
        print(f'calculated (x,y) %.2f cm, %.2f cm' % (calculated_x, calculated_y))
        # print(f'error%% (x,y): %.2f%%, %.2f%%' % (x_error_percent, y_error_percent))
        print(f'disctance error: %f cm' % error_dist)


# the main function has had many purposes, currently, it loops trough all known-location recordings as well as all
# hidden recordings. by commenting or uncommenting debug/plotting functions, as well as by setting debug to True when
# initialising localization, much debug information can be shown it is currently configured to unly output the field
# visualisation and error estimates
#momenteel stukkie wukkie
def test_test():

    y_ref = np.array(wavaudioread("test_recordings/ref_short_testrecordings.wav", 44100))
    loc = Localization(False, y_ref, 1, 200000)

    record_x = [64, 82, 109, 143, 150, 178, 232]
    record_y = [40, 399, 76, 296, 185, 439, 275]

    for i in range(len(record_x)):
        real_x = record_x[i]  # set to any negative value when testing a hidden recording
        real_y = record_y[i]

        filename = "test_recordings/record_x" + str(real_x) + "_y" + str(
            real_y) + ".wav"  # this automatically picks the right file name for known locations

        y = np.array(wavaudioread(filename, 44100))

        calculated_x, calculated_y = loc.locate(y, real_x - 10, real_y - 10)

def EFEF_test():

    y_ref = np.array(wavaudioread("eigen_recordings/newest_short_ref.wav", 44100))
    loc = Localization(False, y_ref, 1, 20000)


    filename = "eigen_recordings/freshest_recording_64-40.wav"
    y = np.array(wavaudioread(filename, 44100))
    real_x = 64 - 10
    real_y = 40 - 10
    calculated_x, calculated_y = loc.locate(y, real_x, real_y)

    filename = "eigen_recordings/freshest_recording_166-390.wav"
    y = np.array(wavaudioread(filename, 44100))
    real_x = 166 - 10
    real_y = 390 - 10
    calculated_x, calculated_y = loc.locate(y, real_x, real_y)

    filename = "eigen_recordings/freshest_recording_352-156.wav"
    y = np.array(wavaudioread(filename, 44100))
    real_x = 352 - 10
    real_y = 156 - 10
    calculated_x, calculated_y = loc.locate(y, real_x, real_y)

    filename = "eigen_recordings/freshest_recording_240-240.wav"
    y = np.array(wavaudioread(filename, 44100))
    real_x = 240 - 10
    real_y = 240 - 10
    calculated_x, calculated_y = loc.locate(y, real_x, real_y)

def jun10_test():

    y_ref = np.array(wavaudioread("ref tests/5000-1000-87.wav", 44100))

    loc = Localization(True, y_ref, 1, 20000)

    record_x = [45, 64, 128, 211, 347, 436]
    record_y = [267, 40, 376, 229, 92, 314]

    for i in range(len(record_x)):
        real_x = record_x[i]
        real_y = record_y[i]

        filename = "verse_recordings/10-jun-x" + str(real_x) + "-y" + str(
            real_y) + ".wav"

        y = np.array(wavaudioread(filename, 44100))

        calculated_x, calculated_y = loc.locate(y, real_x, real_y)


if __name__ == "__main__":

    jun10_test()





