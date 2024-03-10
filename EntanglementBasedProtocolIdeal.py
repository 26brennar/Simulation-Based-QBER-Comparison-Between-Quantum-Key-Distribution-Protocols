#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code for Entanglement-Based Protocol Simulation in an ideal environment.
@author: Brenna Ren
@version: March 9, 2024
"""

from qiskit import *
from IPython.display import display
import numpy as np

# Constants for the protocol:
    
# Number of tests (how many times the protocol will run)
numTests = 10000

# Number of Pairings (length of initial string / 2)
numPairings = 25

# Toggle to show/hide the protocol's details, such as Alice/Bob/Eve's bits, pairings, results, BER
showDetails = False

# Whether Eve is present
evePresent = True


# Creates a 00 (phi+) bell state and returns the quantum circuit
def createBellState(qc, qubit0, qubit1):
    qc.h(qubit0) # Applies Hadamard-gate on qubit 0
    qc.cx(qubit0, qubit1) # Applies CNOT gate on qubit 1 with control as qubit 0
    return qc


# Returns array of encoded bits in bell states
def encodeMessage(bits, pairs):
    # Array for all the quantum circuits
    message = []
    
    for i in range (numPairings):
        # Creates a quantum circuit with 4 qubits and 4 classical registers
        qc = QuantumCircuit(4, 4)
        
        # Makes the actual pairings from the label of 0, 1, or 2
        if (pairs[i] == 0):
            pair1 = [0, 1]
            pair2 = [2, 3]
        elif (pairs[i] == 1):
            pair1 = [0, 2]
            pair2 = [1, 3]
        else:
            pair1 = [0, 3]
            pair2 = [1, 2]
        
        # Generates the phi+ bell state for each pairing
        qc = createBellState(qc, pair1[0], pair1[1])
        qc = createBellState(qc, pair2[0], pair2[1])

        qc.barrier() # Visual barrier in quantum circuit diagrams
        
        # Based on the values of the bits, modifies the phi+ bell state
        if bits[2*i] == 0 and bits[2*i+1] == 0: # -00 = phi+, phi-
            # Creates phi- for the second pairing
            qc.x(pair2[0]) 
        
        elif bits[2*i] == 0 and bits[2*i+1] == 1: # 01 = phi-, phi+
            # Creates phi- for the first pairing
            qc.x(pair1[0])
        
        elif bits[2*i] == 1 and bits[2*i+1] == 0: # 10 = psi+, psi-
            # Creates psi+ for the first pairing
            qc.z(pair1[1])

            # Creates psi- for the second pairing
            qc.z(pair2[0])
            qc.x(pair2[1])
        
        elif bits[2*i] == 1 and bits[2*i+1] == 1: # 11 = psi-, psi+
            # Creates psi- for the first pairing
            qc.z(pair1[0])
            qc.x(pair1[1])

            # Creates psi+ for the second pairing
            qc.z(pair2[1])

        qc.barrier() # Visual barrier in quantum circuit diagrams

        # Add the quantum circuit to the array
        message.append(qc)
        
    return message

# Returns an array of bit values representing the measurements
def decodeMessage(message, pairs):
    results = [] # Array for all the measurements
    for i in range (numPairings):
        qc = message[i]
        
        # Generates pairings based on labels
        if (pairs[i] == 0):
            pair1 = [0, 1]
            pair2 = [2, 3]
        elif (pairs[i] == 1):
            pair1 = [0, 2]
            pair2 = [1, 3]
        else:
            pair1 = [0, 3]
            pair2 = [1, 2]

        # Applies CNOT followed by Hadamard to "undo" the bell-states and allow for easy mapping (00 = phi+, 01 = phi-, 10 = psi+, 11 = psi-)
        qc.cx(pair1[0], pair1[1])
        qc.h(pair1[0])
        qc.cx(pair2[0], pair2[1])
        qc.h(pair2[0])

        # Maps the qubits to their repsective classical registers (based on guessed pairings)
        qc.measure(pair1[0], 3)
        qc.measure(pair1[1], 2)
        qc.measure(pair2[0], 1)
        qc.measure(pair2[1], 0)

        # Code for visualization of quantum circuit:
        # display(qc.draw(output='mpl'))

        # Qiskit qasm simulator
        backend_sim = Aer.get_backend('qasm_simulator')

        # Gets an array of the bit values measured from 1 measurement
        measuredBits = backend_sim.run(qc, shots=1, memory=True).result().get_memory()

        # Maps the 4-bit result to the 4 possible bit combinations
        if (measuredBits[0] == "0001"):
            results.append(0)
            results.append(0)
        elif (measuredBits[0] == "0100"):
            results.append(0)
            results.append(1)
        elif (measuredBits[0] == "1011"):
            results.append(1)
            results.append(0)
        else:
            results.append(1)
            results.append(1)
        
        if (showDetails):
            print("Bob Pairing: " + str(pair1) + " " + str(pair2))
            print(measuredBits)

    return results

# Measures the BER (before discarding)
def measureBER(aliceBits, results):
    BER = 0
    for i in range(numPairings):
        if (aliceBits[2*i] == results[2*i] and aliceBits[2*i+1] == results[2*i+1]):
            BER += 1
    BER /= numPairings
    BER = 1-BER
    
    return BER

# Discards the bits from mismatched pairings and returns the secret key and Alice's original bits for those bits
def discardBits(results, aliceBits, alicePairs, bobPairs):
    newResults = []
    newAliceBits = []
    for i in range(numPairings):
        if (alicePairs[i] == bobPairs[i]):
            newResults.append(results[2*i])
            newResults.append(results[2*i+1])
            newAliceBits.append(aliceBits[2*i])
            newAliceBits.append(aliceBits[2*i+1])
    
    if (showDetails):
        print (newResults)
        print (newAliceBits)

    return newResults, newAliceBits

# Measures the QBER based on the secret key and Alice's original bits
def measureQBER(newResults, newAliceBits):
    if (len(newResults) == 0):
        return 1
    QBER = 0
    for i in range(int(len(newResults) / 2)):
        if (newResults[2*i] == newAliceBits[2*i] and newResults[2*i+1] == newAliceBits[2*i+1]):
            QBER += 1

    QBER /= len(newResults) / 2 
    QBER = 1-QBER
    return QBER

# Simulates the presence of an eavesdropper
def eveMeasureAndDecode(message):
    # Generates Eve's pairings
    evePairs = np.random.randint(3, size=numPairings)
    
    if (showDetails): print ("Eve Pairs:" + str(evePairs))
    
    # Eve's message from intercepting the quantum channel
    eveResults = decodeMessage(message, evePairs)
   
    if (showDetails): print ("Eve Results: " + str(eveResults))
    
    # Eve encodes the message after intercepting it, using her results and her pairings
    eveMessage = encodeMessage(eveResults, evePairs)
    
    return eveMessage

# Runs the entanglement protocol one time
def runProtocol():
    # generate alice's bits (0 or 1).
    # number of bits = 2 * number of pairings.
    aliceBits = np.random.randint(2, size=2*numPairings)
    if (showDetails): print("Alice Bits: " + str(aliceBits))
    
    # generate alice's pairings (labeled as 0, 1, or 2).
    alicePairs = np.random.randint(3, size=numPairings)
    if (showDetails): print("Alice Pairs: " + str (alicePairs))
    
    # encode alice's bits using her pairs
    message = encodeMessage(aliceBits, alicePairs)
    if (showDetails): print()
    
    if (evePresent):
        message = eveMeasureAndDecode(message)
        if (showDetails): print()
    
    # generate bob's pairings (0, 1, or 2)
    bobPairs = np.random.randint(3, size=numPairings)
    if (showDetails): print ("Bob Pairs: " + str(bobPairs))
    
    # decode the message
    bobResults = decodeMessage(message, bobPairs)
    if (showDetails): print ("Bob Results: " + str(bobResults))
    
    # measure BER
    BER = measureBER(aliceBits, bobResults)
    
    # get the secret key
    newResults, newAliceBits = discardBits(bobResults, aliceBits, alicePairs, bobPairs)
    
    # measure the QBER of the secret key
    QBER = measureQBER(newResults, newAliceBits)
    # QBER = -1
    
    if (showDetails): 
        print("BER: " + str(BER))
        print("QBER: " + str(QBER))
    return QBER

# Average QBER across all the tests
avgQBER = 0

# Array of all of the QBERs for each of the tests
allQBER = []

f = open("EntanglementResultsIdeal.txt", "w")

# run the protocol for however many tests there are
for i in range (numTests):
    QBER = runProtocol()
    avgQBER += QBER
    allQBER.append(QBER)
    f.write(str(QBER) + "\n")
    print ("Finshed Test " + str(i+1))

f.close()
# get average QBER
avgQBER /= numTests

print ("Average QBER for " + str(numPairings*2) + " bits across " + str(numTests) + " runs: " + str(avgQBER))
print ("All QBERs: " + str(allQBER))
