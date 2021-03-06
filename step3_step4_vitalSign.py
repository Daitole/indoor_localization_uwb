from scipy.io import loadmat
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy.fftpack import fft
import pandas as pd

breathRate = np.zeros((6, 7))
rCnt, cCnt = -1, -1
# range_bin value to focus for each eadar
rangeRef = {'Radar 1': [0.8128, 1.8168], 'Radar 2': [1.3716, 3.0861], 'Radar 3': [1.1303, 2.8448]}
fileRef = {'time': '/t_stmp.mat', 'bin': 'range_bins.mat', 'mag': 'rawscans.mat'}
radarRef = {'time': 't_stmp', 'bin': 'range_bins', 'mag': 'rawscans'}
# signal trim indices
signalTrimRef = {
                'Radar 1': {
                'BR_st1': {'browsing': [20, 40], 'fetal_left': [15, 60], 'fetal_right': [15, 60], 'freefall': [0, 55], 'left_turned': [20, 60], 'right_turned': [10, 60]}, 
                'BR_st2': {'browsing': [20, 29], 'fetal_left': [15, 60], 'fetal_right': [10, 40], 'freefall': [37, 55], 'left_turned': [33, 50], 'right_turned': [10, 35], 'soldier': [21, 60]} 
                },
                'Radar 2': {
                'BR_st1': {'fetal_left': [26, 60], 'fetal_right': [6, 60], 'left_turned': [10, 60], 'right_turned': [10, 60], 'soldier': [26, 55]}, 
                'BR_st2': {'browsing': [17, 29], 'fetal_left': [25, 55], 'fetal_right': [15, 55], 'freefall': [20, 75], 'left_turned': [10, 55], 'right_turned': [0, 40], 'soldier': [15, 60]} 
                },
                'Radar 3': {
                'BR_st1': {'browsing': [30, 55], 'fetal_left': [10, 60], 'fetal_right': [25, 60], 'freefall': [10, 55], 'left_turned': [10, 60], 'right_turned': [10, 60], 'soldier': [10, 55]}, 
                'BR_st2': {'fetal_left': [25, 55], 'fetal_right': [10, 45], 'freefall': [20, 75], 'left_turned': [15, 50], 'right_turned': [5, 30], 'soldier': [30, 60]} 
                }
                }

pre_path = './DataSet/Vital Sign/'
for radar in ['Radar 1', 'Radar 2', 'Radar 3']:
    for participant in ['BR_st1', 'BR_st2']:
        rCnt += 1
        for pattern in ['browsing', 'fetal_left', 'fetal_right', 'freefall', 'left_turned', 'right_turned', 'soldier']:
            cCnt += 1
            radarData = {}
            for files in fileRef:
                # load .mat files
                radarData[files] = loadmat(pre_path + participant + '/' + radar + '/' + pattern + '/' + fileRef[files])[radarRef[files]]
                if files == 'time' or files == 'bin':
                    radarData[files] = radarData[files].flatten()
            
            # indices of range_bins falling in the range
            binIdx = np.where(np.logical_and(radarData['bin'] > rangeRef[radar][0], radarData['bin'] < rangeRef[radar][1]))
            signal = [] 
            # iterating through each scan
            iterations = np.shape(radarData['mag'])[0]
            for i in range(iterations):
                # maximum amplitude at the focused range bins
                maxVal = np.max(radarData['mag'][i, :][binIdx])
                signal.append(maxVal)
            
            timeElapsed = radarData['time'][-1] - radarData['time'][0]
            sampleRate = timeElapsed/iterations

            # trim signal
            signal = np.asarray(signal)
            trimStart = 0
            trimEnd = timeElapsed
            if pattern in signalTrimRef[radar][participant]:
                trimStart = signalTrimRef[radar][participant][pattern][0]
                trimEnd = signalTrimRef[radar][participant][pattern][1]
                iterStart = trimStart*iterations//timeElapsed
                iterEnd = trimEnd*iterations//timeElapsed
                signal = signal[iterStart: iterEnd + 1]
                iterations = len(signal)
            
            # normalizing the signal
            signal = np.subtract(signal, np.mean(signal))

            # FFT with the hamming function
            signalFFT = fft(np.multiply(signal, np.hamming(iterations)))
            # multiply freq by 60 to compute breaths/min
            freqs = np.multiply(np.linspace(0.0, 1.0/(2.0*sampleRate), iterations//2), 60)
            signalFFT = 2.0/iterations * np.abs(signalFFT[0:iterations//2])

            # corresponding frequency bins
            idx = np.where(freqs < 90)[0][-1]
            freqs = freqs[:idx]
            signalFFT = signalFFT[:idx]
            breathRate[rCnt, cCnt] = str(freqs[np.argmax(signalFFT)])
            
            # plotting the signal and the FFT
            plt.figure()
            plt.subplot(211)
            plt.plot(np.linspace(trimStart, trimEnd,iterations), signal)
            plt.title('Time Domain - Breathing Signal')
            plt.xlabel('Time Elapsed (in Seconds)')
            plt.ylabel('Magnitude')

            plt.subplot(212)
            plt.plot(freqs, signalFFT)
            plt.title('Freq Domain - FFT Breathing Signal')
            plt.xlabel('Frequency (breaths per min)')
            plt.ylabel('Magnitude')
            plt.subplots_adjust(hspace=0.5)

            plt.suptitle(radar + ' Participant: ' + participant + '  Activity: ' + pattern)
            plt.savefig('./vital_sign_plots/' + radar + ' ' + participant + '_' + pattern + '.png', bbox_inches="tight")
            plt.close()

        cCnt = -1

# summary of estimated breathing rates
df = pd.DataFrame(breathRate, columns=['browsing', 'fetal_left', 'fetal_right', 'freefall', 'left_turned', 'right_turned', 'soldier'], index=['Radar 1 BR_st1', 'Radar 1 BR_st2', 'Radar 2 BR_st1', 'Radar 2 BR_st2', 'Radar 3 BR_st1', 'Radar 3 BR_st2'])
print(df)
