#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code for BB84 Simulation in an ideal environment.
@author: Brenna Ren
@version: March 9, 2024
"""

from qiskit import QuantumCircuit, Aer, transpile
from qiskit.visualization import plot_histogram, plot_bloch_multivector
from matplotlib import pyplot
import numpy as np

numTests = 10000
numBits = 50

avgQBER = 0

def encode_message(bits, bases):
    message = []
    for i in range(numBits):
        # Prepare a quantum circuit with one qubit and one classical register
        qc = QuantumCircuit(1,1)

        # If the encoding basis is +
        if bases[i] == 0: # Prepare qubit in Z-basis
            if bits[i] == 0:
                pass # No change to qubits (identity matrix)
            else:
                qc.x(0) # Applies X-gate on first qubit (qubit 0)

        # If the encoding basis is X
        else: # Prepare qubit in X-basis
            if bits[i] == 0:
                qc.h(0) # Applies Hadamard gate on first qubit (qubit 0)
            else:
                qc.x(0) # Applies X-gate on first qubit (qubit 0)
                qc.h(0) # Applies Hadamard gate on first qubit (qubit 0)
        
        qc.barrier() # Visual barrier in quantum circuit diagrams

        # Add the quantum circuit to the array
        message.append(qc)
    return message

def measure_message(message, bases):
    measurements = [] # Array of all measurements
    for q in range(numBits):
        qc = message[q]

        # If the guessed basis is +
        if bases[q] == 0: # measuring in Z-basis
            qc.measure(0,0) # Maps classical register 0 to qubit 0

        # If the guessed basis is X
        if bases[q] == 1: # measuring in X-basis
            qc.h(0) # Applies H-gate on qubit 0 to simulate decoding in X-basis
            qc.measure(0,0) # Maps classical register 0 to qubit 0

        # Qiskit qasm simulator
        backend_sim = Aer.get_backend('qasm_simulator')

        # Gets an array of the bit values measured from 1 measurement
        measuredBits = backend_sim.run(qc, shots=1, memory=True).result().get_memory()
        
        # Qubit 0's measurement
        measured_bit = int(measuredBits[0])

        # Adds the measurement to the array
        measurements.append(measured_bit)

        # Code for visualization of quantum circuit:
        # display(message[q].draw(output='mpl'))
    return measurements

# Returns the secret key and Alice's original bits for those bits
def discardBits(results, aliceBits, aliceBases, bobBases):
    newResults = [] # Array for the secret key
    newAliceBits = [] # Array for Alice's bases after discarding
    for i in range(numBits):

        # If Alice and Bob's bases are the same (not mismatched)
        if (aliceBases[i] == bobBases[i]):
            newResults.append(results[i])
            newAliceBits.append(aliceBits[i])

    return newResults, newAliceBits

# Returns the QBER (number of correct bits / number of bits in secret key)
def measureQBER(newResults, newAliceBits):

    # If all of Alice's and Bob's pairings are mismatched, the secret key is an empty string
    if (len(newResults) == 0):
        return "null"

    # Finds the QBER by summing the incorrect bits and dividing by total number of bits
    QBER = 0
    for i in range(int(len(newResults))):
        if (newResults[i] != newAliceBits[i]):
            QBER += 1

    QBER /= len(newResults)
    return QBER

def runProtocol():
    # Generate Alice's bits, generates bases, and encodes her bits
    alice_bits = np.random.randint(2, size=numBits)
    alice_bases = np.random.randint(2, size=numBits)
    message = encode_message(alice_bits, alice_bases)

    # OMIT IF EVE IS NOT PRESENT
    # Generate Eve's bases, measure the message, and encode the message again
    eve_bases = np.random.randint(2, size=numBits)
    intercepted_message = measure_message(message, eve_bases)
    new_message = encode_message(intercepted_message, eve_bases)
    
    # Generate Bob's bases and measure the message
    bob_bases = np.random.randint(2, size=numBits)
    bob_results = measure_message(new_message, bob_bases)
    
    # get the secret key
    newResults, newAliceBits = discardBits(bob_results, alice_bits, alice_bases, bob_bases)
    
    # measure the QBER of the secret key
    QBER = measureQBER(newResults, newAliceBits)
    
    return QBER

allQBER = []
f = open("BB84ResultsIdeal.txt", "w")
for t in range(numTests):
    QBER = runProtocol()
    
    while (QBER == "null"):
        QBER = runProtocol()
    
    print ("Finished Test " + str(t+1))
    
    avgQBER += QBER
    allQBER.append(QBER)
    f.write(str(QBER) + "\n")
    
    
f.close()
avgQBER /= numTests

print ("\rAverage QBER: " + str(avgQBER))
