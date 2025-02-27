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

def build_upchirp(chirp, id, sf, os_factor=1):
    N = 2 ** sf
    print("id")
    print(id)
    n_fold = int(N * os_factor - id * os_factor)
    for n in range(int(N * os_factor)):
        if n < n_fold:
            chirp[n] = 1.0 + 0.0j
            chirp[n] *= np.exp(2.0j * np.pi * (n * n / (2 * N) / (os_factor ** 2) + (id / N - 0.5) * n / os_factor))
            # print(n)
            # print(chirp[n])
        else:
            chirp[n] = 1.0 + 0.0j
            chirp[n] *= np.exp(2.0j * np.pi * (n * n / (2 * N) / (os_factor ** 2) + (id / N - 1.5) * n / os_factor))

def build_ref_chirps(upchirp, downchirp, sf, os_factor=1):
    N = 2 ** sf
    build_upchirp(upchirp, 0, sf, os_factor)
    for i in range(len(downchirp)):
        downchirp[i] = np.conjugate(upchirp[i])

def generate_reference_output(ref_out, preamb_samp_cnt, output_offset, m_sync_words, m_preamb_len, m_samples_per_symbol, sf, os_factor, m_upchirp, m_downchirp, src_data):

    if len(m_sync_words) == 1:
        tmp = m_sync_words[0]
        m_sync_words.extend([0, 0])
        m_sync_words[0] = ((tmp & 0xF0) >> 4) << 3
        m_sync_words[1] = (tmp & 0x0F) << 3

    for i in range(m_preamb_len):
        ref_out[output_offset:output_offset + m_samples_per_symbol] = m_upchirp
        
        output_offset += m_samples_per_symbol
        preamb_samp_cnt += m_samples_per_symbol
    
    if preamb_samp_cnt == (m_preamb_len * m_samples_per_symbol):
        # sync words
        temp1_chirp = [0j] * 512
        build_upchirp(temp1_chirp, m_sync_words[0], sf, os_factor)
        ref_out[output_offset:output_offset + m_samples_per_symbol] = temp1_chirp
        output_offset += m_samples_per_symbol
        preamb_samp_cnt += m_samples_per_symbol

    if preamb_samp_cnt == (m_preamb_len + 1) * m_samples_per_symbol:
        temp_chirp = [0j] * 512
        build_upchirp(temp_chirp, m_sync_words[1], sf, os_factor)
        ref_out[output_offset:output_offset + m_samples_per_symbol] = temp_chirp
        output_offset += m_samples_per_symbol
        preamb_samp_cnt += m_samples_per_symbol
    
    if preamb_samp_cnt < (m_preamb_len + 4) * m_samples_per_symbol:
        # 2.25 downchirps
        ref_out[output_offset:output_offset +  m_samples_per_symbol] = m_downchirp
        output_offset += m_samples_per_symbol
        preamb_samp_cnt += m_samples_per_symbol

    if preamb_samp_cnt < (m_preamb_len + 4) * m_samples_per_symbol:
        # 2.25 downchirps
        ref_out[output_offset:output_offset +  m_samples_per_symbol] = m_downchirp
        output_offset += m_samples_per_symbol
        preamb_samp_cnt += m_samples_per_symbol

    if preamb_samp_cnt == (m_preamb_len + 4) * m_samples_per_symbol:
        ref_out[output_offset:output_offset + m_samples_per_symbol // 4] = m_downchirp[:m_samples_per_symbol // 4]
        output_offset += m_samples_per_symbol // 4
    
    for i in range(len(src_data)):
        temp2_chirp = [0j] * 512
        build_upchirp(temp2_chirp, src_data[i], sf, os_factor)
        ref_out[output_offset:output_offset + m_samples_per_symbol] = temp2_chirp
        output_offset += m_samples_per_symbol

    return ref_out


class qa_modulate(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_function_test(self):

        sf = 7
        samp_rate = 500000
        bw = 125000
        cr = 2

        relative_path = "qa_ref/qa_ref_tx_no_mod/ref_tx_sf"+str(sf)+"_cr"+str(cr)+".bin"
        source_path = os.path.join(script_dir, relative_path)
        blocks_file_source = blocks.file_source(gr.sizeof_int*1, source_path, False, 0, 0)
        blocks_file_source.set_begin_tag(pmt.PMT_NIL)
        #blocks_vector_source = blocks.vector_source_i(src_data, False, 1, [])
        blocks_throttle = blocks.throttle(gr.sizeof_gr_complex*1, (samp_rate*10),True)
        lora_sdr_modulate = lora_sdr.modulate(sf, samp_rate, bw, [0x12], (int(20*2**sf*samp_rate/bw)),8)
        blocks_vector_sink = blocks.vector_sink_c(1, 1024)
        #dst = blocks.null_sink(gr.sizeof_char)
        self.tb.connect((blocks_file_source, 0), (lora_sdr_modulate, 0))
        self.tb.connect((lora_sdr_modulate, 0), (blocks_throttle, 0))
        self.tb.connect((blocks_throttle, 0), (blocks_vector_sink, 0))
     
        self.tb.run()
        #self.tb.run()
        result_data = blocks_vector_sink.data()
        
        relative_path2 = "qa_ref/qa_ref_mod/ref_tx_sf"+str(sf)+"_cr"+str(cr)+".bin"
        reference_path = os.path.join(script_dir, relative_path2)
        f = open(reference_path,"rb")
        ref_data = np.fromfile(f, dtype=np.complex64)
        f.close()

        self.assertEqual(result_data, list(ref_data))

    def test_002_function_test(self):
        # set the payload length randomly between 0 and 17. 17 is set due to the buffer in modulate block, if n_frames is set to 1, the maximum output number is 15360. 15360 extracts 8 header, 2 upchirp, 2.5 down chirp, has only 17.75 symbols left.
        payload_length = 7
        # nibbles generated by whitening block is 4 bits, the maximum value of the nibble is 16
        max_value = 16

        # randomly generate the nibbles output by whitening block
        src_data = np.random.randint(max_value, size=payload_length)
        
        src_tags = [make_tag('frame_len',payload_length ,0,'src_data')]
        
        sf = 7
        m_number_of_bins = 2 ** sf
        samp_rate = 500000

        bw = 125000
        os_factor = samp_rate / bw
        blocks_vector_source = blocks.vector_source_i(src_data, False, 1, src_tags)
        blocks_throttle = blocks.throttle(gr.sizeof_gr_complex*1, (samp_rate*10),True)
        lora_sdr_modulate = lora_sdr.modulate(sf, samp_rate, bw, [0x12], (int(20*2**sf*samp_rate/bw)),8)
        blocks_vector_sink = blocks.vector_sink_c(1, 1024)
        #dst = blocks.null_sink(gr.sizeof_char)
        self.tb.connect((blocks_vector_source, 0), (lora_sdr_modulate, 0))
        self.tb.connect((lora_sdr_modulate, 0), (blocks_throttle, 0))
        self.tb.connect((blocks_throttle, 0), (blocks_vector_sink, 0))
     
        self.tb.run()
        
        result_data = blocks_vector_sink.data()

        # generate the reference output

        ref_out = [0j] * len(result_data)
        preamb_samp_cnt = 0
        m_preamb_len = 8
        m_samples_per_symbol = int(os_factor*m_number_of_bins)
        output_offset = 0
        m_sync_words = [8,16]
        m_upchirp = [0j] * m_samples_per_symbol
        m_downchirp = [0j] * m_samples_per_symbol
        build_ref_chirps(m_upchirp, m_downchirp, sf, os_factor)
        ref_out = generate_reference_output(ref_out, preamb_samp_cnt, output_offset, m_sync_words, m_preamb_len, m_samples_per_symbol, sf, os_factor, m_upchirp, m_downchirp, src_data)
        decimalPlace = 4
        message = "the two is not equal on the 4th decimal place"
        print(len(result_data))
        for i in range(len(result_data)):
            
            self.assertAlmostEqual(result_data[i], ref_out[i], decimalPlace, message)

        #self.assertEqual(rounded_result, rounded_ref)
    

if __name__ == '__main__':
    gr_unittest.run(qa_modulate)
