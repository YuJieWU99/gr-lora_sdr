##############################################################################
# File: qa_hamm.py
# Date: 21-12-2023
#
# Description: This is a test code for block hamming_enc
#
# Function: int_to_bool
#   Description:convert an integer (value) into a list of boolean values, 
#            where each boolean represents a bit in the binary representation 
#            of the integer. The function 
#   Input: the integer value, num_bits(the number of bits)  
#   Output: list - a list of boolean values representing the binary
#
# Function: hamming_encode
#   Description: Encode a sequence of source data using Hamming coding.
#                The function adds parity bits to the data 
#   Input: sf (int) - Spreading factor, cr (int) - Coding rate, src_data (list) 
#   Output: list - Encoded data with added parity bits
#
# Function: test_001_functional_test
#    Description: test the correctness of parity bits generated by hamming_enc
#
##############################################################################


from gnuradio import gr, gr_unittest
from gnuradio import blocks
from numpy import array
from whitening_sequence import code
import numpy as np

try:
    import gnuradio.lora_sdr as lora_sdr
   
except ImportError:
    import os
    import sys
    dirname, filename = os.path.split(os.path.abspath(__file__))
    sys.path.append(os.path.join(dirname, "bindings"))

def int_to_bool(value, num_bits):

    return [(value >> i) & 1 for i in range(num_bits - 1, -1, -1)]

def hamming_encode(sf, cr, src_data):

    data_bin = []
    ref_out = [0] * len(src_data)
    p0, p1, p2, p3, p4 = False, False, False, False, False
    m_cnt = 0

    for i in range(len(src_data)):

        cr_app = 4 if m_cnt < sf - 2 else cr
        data_bin = int_to_bool(src_data[i], 4)

        # the data_bin is msb first
        if cr_app != 1:
            p0 = data_bin[3] ^ data_bin[2] ^ data_bin[1]
            p1 = data_bin[2] ^ data_bin[1] ^ data_bin[0]
            p2 = data_bin[3] ^ data_bin[2] ^ data_bin[0]
            p3 = data_bin[3] ^ data_bin[1] ^ data_bin[0]

            # we put the data LSB first and append the parity bits
            ref_out[i] = ((data_bin[3] << 7) | (data_bin[2] << 6) | (data_bin[1] << 5) |
                            (data_bin[0] << 4) | (p0 << 3) | (p1 << 2) | (p2 << 1) | p3) >> (4 - cr_app)
        else:
            # coding rate = 4/5, add a parity bit
            p4 = data_bin[0] ^ data_bin[1] ^ data_bin[2] ^ data_bin[3]
            ref_out[i] = ((data_bin[3] << 4) | (data_bin[2] << 3) | (data_bin[1] << 2) |
                            (data_bin[0] << 1) | p4)

        m_cnt += 1
    
    return ref_out

class qa_hamm(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_functional_test(self):

        sf = 7
        cr = 2
        # set the payload_length
        payload_length = 5
        # a nibble has 4 bits so that the maximum value for the nibble is 15
        max_value = 16 
        # randomly generate the source data
        src_data = np.random.randint(max_value, size=payload_length)

        # initialize the blocks
        lora_sdr_hamming_enc = lora_sdr.hamming_enc(cr, sf)
        blocks_vector_source = blocks.vector_source_b(src_data, False, 1, [])
        blocks_vector_sink = blocks.vector_sink_b(1, 1024)

        # connect the blocks
        self.tb.connect((blocks_vector_source, 0), (lora_sdr_hamming_enc, 0))
        self.tb.connect((lora_sdr_hamming_enc, 0), (blocks_vector_sink, 0))
        self.tb.run()

        # get the output from the connected blocks
        result_data = blocks_vector_sink.data()

        # generate reference data
        ref_data = hamming_encode(sf,cr,src_data)

        self.assertEqual(ref_data, result_data)
    

if __name__ == '__main__':
    gr_unittest.run(qa_hamm)
