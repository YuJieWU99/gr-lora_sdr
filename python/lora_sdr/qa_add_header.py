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

def make_tag_string(key, value, offset, srcid=None):
    tag = gr.tag_t()
    tag.key = pmt.string_to_symbol(key)
    # Convert elements of 'value' to strings before using string_to_symbol
    value_strings = [str(v) for v in value]
    tag.value = pmt.string_to_symbol(value_strings[0])
    tag.offset = offset
    if srcid is not None:
        tag.srcid = pmt.to_pmt(srcid)
    return tag

def get_header_ref(cr, has_crc, nitems_in_frame, src_data):
            # calculate the header
    ref_out = [0] * (5 + nitems_in_frame)
    m_header = [0] * 5
    m_header[0] = int(nitems_in_frame/2) >> 4
    m_header[1] = int(nitems_in_frame/2) & 0x0F
    m_header[2] = (cr << 1) | has_crc

    c4 = (m_header[0] & 0b1000) >> 3 ^ (m_header[0] & 0b0100) >> 2 ^ (m_header[0] & 0b0010) >> 1 ^ (m_header[0] & 0b0001)
    c3 = (m_header[0] & 0b1000) >> 3 ^ (m_header[1] & 0b1000) >> 3 ^ (m_header[1] & 0b0100) >> 2 ^ (m_header[1] & 0b0010) >> 1 ^ (m_header[2] & 0b0001)
    c2 = (m_header[0] & 0b0100) >> 2 ^ (m_header[1] & 0b1000) >> 3 ^ (m_header[1] & 0b0001) ^ (m_header[2] & 0b1000) >> 3 ^ (m_header[2] & 0b0010) >> 1
    c1 = (m_header[0] & 0b0010) >> 1 ^ (m_header[1] & 0b0100) >> 2 ^ (m_header[1] & 0b0001) ^ (m_header[2] & 0b0100) >> 2 ^ (m_header[2] & 0b0010) >> 1 ^ (m_header[2] & 0b0001)
    c0 = (m_header[0] & 0b0001) ^ (m_header[1] & 0b0010) >> 1 ^ (m_header[2] & 0b1000) >> 3 ^ (m_header[2] & 0b0100) >> 2 ^ (m_header[2] & 0b0010) >> 1 ^ (m_header[2] & 0b0001)

    m_header[3] = c4
    m_header[4] = c3 << 3 | c2 << 2 | c1 << 1 | c0 
    ref_out = m_header + src_data
    return ref_out


class qa_add_header(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_functional_test(self):

        sf = 7
        impl_head = False
        has_crc = True
        cr = 2
        # payload_length is the length of source frame, set the value randomly
        payload_length = 4
        # nitems_in_frame is the length of message after whitening block which is twice of the source
        nitems_in_frame = payload_length * 2 
        # nibbles generated by whitening block is 4 bits, the maximum value of the nibble is 16
        max_value = 16

        # randomly generate the nibbles output by whitening block
        src_whitening = np.random.randint(max_value, size=payload_length)
        src_after_w = [0] * (nitems_in_frame)
        src_after_w = [src_whitening[i] ^ code[i] for i in range(len(src_whitening))]
        src_data = []

        for value in src_after_w:
            hex_string = format(value, '02x')  # Convert the byte to a two-digit hexadecimal string
            src_data.extend([int(digit, 16) for digit in hex_string]) # append src_data to the corresponding integer as the input of vector_source

        # Convert each integer to a string and join them
        src = ''.join(map(str, src_whitening))
        src_tags = [make_tag('frame_len',nitems_in_frame, 0,'src_data'),make_tag_string('payload_str',src,0,'src')] 

        lora_sdr_header = lora_sdr.header(impl_head, has_crc, cr)
        blocks_vector_source = blocks.vector_source_b(src_data, False, 1, src_tags)
        blocks_vector_sink = blocks.vector_sink_b(1, 1024)


        self.tb.connect((blocks_vector_source, 0), (lora_sdr_header, 0))
        self.tb.connect((lora_sdr_header, 0), (blocks_vector_sink, 0))
        self.tb.run()
        
        ref_out = get_header_ref(cr, has_crc, nitems_in_frame, src_data)

        result_data = blocks_vector_sink.data()

        # Load ref files
        self.assertEqual(result_data, ref_out)

           
if __name__ == '__main__':
    gr_unittest.run(qa_add_header)
