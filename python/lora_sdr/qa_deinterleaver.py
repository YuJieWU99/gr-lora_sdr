#!/usr/bin/env python
# -*- coding: utf-8 -*-
#                     GNU GENERAL PUBLIC LICENSE
#                        Version 3, 29 June 2007
#
#  Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
#  Everyone is permitted to copy and distribute verbatim copies
#  of this license document, but changing it is not allowed.


from gnuradio import gr, gr_unittest
from gnuradio import blocks
from numpy import array
from whitening_sequence import code
import pmt
import numpy as np
import time
import os
import sys


# from gnuradio import blocks
try:
    import gnuradio.lora_sdr as lora_sdr
    
except ImportError:
    import os
    import sys
    dirname, filename = os.path.split(os.path.abspath(__file__))
    sys.path.append(os.path.join(dirname, "bindings"))

script_dir = os.path.dirname(os.path.abspath(__file__))
def make_tag(key, value, offset, srcid=None):
    tag = gr.tag_t()
    tag.key = pmt.string_to_symbol(key)
    tag.value = pmt.to_pmt(value)
    tag.offset = offset
    if srcid is not None:
        tag.srcid = pmt.to_pmt(srcid)
    return tag

import numpy as np

def int2bool(integer, n_bits):
    vec = [(integer >> i) & 1 for i in range(n_bits - 1, -1, -1)]

    return vec

def bool2int(b):
    integer = sum(bit << i for i, bit in enumerate(reversed(b)))
    return integer

def mod(a, b):
    return a % b

def process_data(in_data, m_sf, m_cr, m_ldro, m_frame_len):
    
    nitems_to_process = len(in_data)
    out_data = []
    cw_cnt = 0
    while cw_cnt in range(m_frame_len):
    
        cw_len = 4 + (4 if cw_cnt< m_sf - 2 else m_cr)
        sf_app = m_sf - 2 if (cw_cnt < m_sf - 2) or m_ldro else m_sf
       
        nitems_to_process = np.minimum(nitems_to_process,sf_app)
   

        if nitems_to_process >= sf_app or cw_cnt + nitems_to_process == m_frame_len :

        # Create the empty matrices

            cw_bin = [int2bool(0, cw_len) for _ in range(sf_app)]
            init_bit = [0] * m_sf
            inter_bin = [init_bit.copy() for _ in range(cw_len)]


            # Convert input codewords to binary vector of vector
            for i in range(sf_app):
                if i >= nitems_to_process:
                    cw_bin[i] = int2bool(0, cw_len)
        
                else:
                    cw_bin[i] = int2bool(in_data[i], cw_len)
              
                cw_cnt += 1
                
           
            for i in range(cw_len):
                for j in range(sf_app):
                    inter_bin[i][j] = cw_bin[mod((i - j - 1), sf_app)][i]
                    
                
                # For the first block, add a parity bit and a zero at the end of the LoRa symbol (reduced rate)
                if cw_cnt == m_sf - 2 or m_ldro:
                    inter_bin[i][sf_app] = sum(inter_bin[i]) % 2
        
              
                out_data.append(bool2int(inter_bin[i]))
            in_data = in_data[nitems_to_process:]
            nitems_to_process = m_frame_len - nitems_to_process

            
    
    return out_data


class qa_deinterleaver(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_functional_test(self):

        sf = 7
        cr = 2
        max_value = 16
        sf = 11
        ldro = False
        # define payloadlength
        payload_length = 10
        # nibbles generated by whitening block is 4 bits, the maximum value of the nibble is 16
        max_value = 16

        # randomly generate the input data
        src_data = np.random.randint(max_value, size=payload_length)
        # print(src_data)

        src_tags = [make_tag('frame_len',payload_length, 0,'src_data')] 
        blocks_vector_source = blocks.vector_source_b(src_data, False, 1, src_tags)
    
        lora_sdr_interleaver = lora_sdr.interleaver(cr, sf, ldro, 125000)
        blocks_vector_sink = blocks.vector_sink_i(1, 1024)      

        self.tb.connect((blocks_vector_source, 0), (lora_sdr_interleaver, 0))
        self.tb.connect((lora_sdr_interleaver , 0), (blocks_vector_sink, 0))
        self.tb.run()

        result_data = blocks_vector_sink.data()
        # generate reference interleaver
        ref_out = process_data(src_data, sf, cr,ldro, payload_length)

        self.assertEqual(result_data, ref_out)

    
if __name__ == '__main__':
    gr_unittest.run(qa_deinterleaver)