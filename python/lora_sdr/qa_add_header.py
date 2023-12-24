##############################################################################
# File: qa_add_header.py
# Date: 21-12-2023
#
# Description: This is a test code for block add_header
#
# Function: make_tag
#   Description: Create a GNU Radio tag with specified key, value, offset, and optional source ID.
#   Input: key (str) - Key for the tag, value - Value for the tag, 
#          offset (int) - Offset of the tag in intput data, srcid (optional) - Source ID for the tag, default is None
#   Output: gr.tag_t - GNU Radio tag object with specified attributes
#
# Function: make_tag_string
#   Description: Create a GNU Radio tag with specified key, value(str), offset, and optional source ID.
#   Input: key (str) - Key for the tag, value - Value for the tag, 
#          offset (int) - Offset of the tag in intput data, srcid (optional) - Source ID for the tag, default is None
#   Output: gr.tag_t - GNU Radio tag object with specified attributes
#
# Function: get_header_ref
#   Function: Calculate the header for a LoRa packet based on specified parameters.
#   Input:
#     cr (int) - Coding rate,
#     has_crc (bool) - Indicator for CRC presence,
#     nitems_in_frame (int) - Length of the frame,
#     src_data (list) - Source data
#   Output:
#     list - Complete header for the LoRa packet
#
# Function: test_001_functional_test
#    Description: test the correctness of adding header to message output from 
#                whitening block, when there is crc
##############################################################################



from gnuradio import gr, gr_unittest
from gnuradio import blocks
from numpy import array
from whitening_sequence import code
import pmt
import numpy as np
import os
import sys

try:
    import gnuradio.lora_sdr as lora_sdr
    
except ImportError:
    import os
    import sys
    dirname, filename = os.path.split(os.path.abspath(__file__))
    sys.path.append(os.path.join(dirname, "bindings"))

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

        impl_head = False
        has_crc = True
        cr = 2
        # payload_length is the length of source frame, set the value randomly
        payload_length = 4
        # nitems_in_frame is the length of message after whitening block which is twice of the source
        nitems_in_frame = payload_length * 2 
        # nibbles generated by whitening block is 4 bits, the maximum value of the nibble is 15
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

        # initialize the blocks
        lora_sdr_header = lora_sdr.header(impl_head, has_crc, cr)
        blocks_vector_source = blocks.vector_source_b(src_data, False, 1, src_tags)
        blocks_vector_sink = blocks.vector_sink_b(1, 1024)

        # connect the blocks
        self.tb.connect((blocks_vector_source, 0), (lora_sdr_header, 0))
        self.tb.connect((lora_sdr_header, 0), (blocks_vector_sink, 0))
        self.tb.run()
        
        # get the output from the connected blocks
        result_data = blocks_vector_sink.data()

        # generate reference data
        ref_data = get_header_ref(cr, has_crc, nitems_in_frame, src_data)

        self.assertEqual(result_data, ref_data)

           
if __name__ == '__main__':
    gr_unittest.run(qa_add_header)
