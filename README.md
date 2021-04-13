[![GitHub last commit](https://img.shields.io/github/last-commit/tapparelj/gr-lora_sdr)](https://img.shields.io/github/last-commit/tapparelj/gr-lora_sdr)
[![arXiv](https://img.shields.io/badge/arXiv-2002.08208-<COLOR>.svg)](https://arxiv.org/abs/2002.08208)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) 
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2Ftapparelj%2Fgr-lora_sdr&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://hits.seeyoufarm.com)


## Summary
This is the fully-functional GNU Radio software-defined radio (SDR) implementation of a LoRa transceiver with all the necessary receiver components to operate correctly even at very low SNRs. The transceiver is available as a module for GNU Radio 3.8. This work has been conducted at the Telecommunication Circuits Laboratory, EPFL. 

In the GNU Radio implementation of the LoRa Tx and Rx chains the user can choose all the parameters of the transmission, such as the spreading factor, the coding rate, the bandwidth, the sync word, the presence of an explicit header and CRC.

-   In the Tx chain, the implementation contains all the main blocks of the LoRa transceiver: the header- and the CRC-insertion blocks, the whitening block, the Hamming encoder block, the interleaver block, the Gray mapping block, and the modulation block.
-   On the receiver side there is the packet synchronization block, which performs all the necessary tasks needed for the synchronization, such as the necessary STO and CFO estimation and correction. The demodulation block follows, along with the Gray demapping block, the deinterleaving block, the Hamming decoder block and the dewhitening block, as well as a CRC block.
-   The implementation can be used for fully end-to-end experimental performance results of a LoRa SDR receiver at low SNRs.



## Single user Functionalities:

- Sending and receiving LoRa packets between USRP-USRP and USRP-commercial LoRa transceiver (tested for Adafruit Feather 32u4 RFM95 and dragino LoRa/GPS HAT).

- Parameters available:
	- Spreading factors: 7-12 (without reduce rate mode)
	- Coding rates: 0-4
	- Implicit and explicit header mode
	- Payload length: 1-255 bytes
	- sync word selection (network ID)
	- Verification of payload CRC
	- Verification of explicit header checksum
## Reference

J. Tapparel, O. Afisiadis, P. Mayoraz, A. Balatsoukas-Stimming, and A. Burg, “An Open-Source LoRa Physical Layer Prototype on GNU Radio”

[https://arxiv.org/abs/2002.08208](https://arxiv.org/abs/2002.08208)

If you find this implementation useful for your project, please consider citing the aforementioned paper.

## Prerequisites
- Gnuradio 3.8.2
- python 3
- cmake
- swig
- libvolk
- Boost
- UHD
- gcc
- gxx

The conda environment used to develop this module is described by the environment.yml file. 
## Installation:
- Download the zip archive and extract it
- The GNU Radio OOT module can be build with:
		
	```sh
	cd [path to gr-lora_sdr]
	mkdir build
	cd build
	cmake ..  -DCMAKE_INSTALL_PREFIX={your prefix} # default to usr/local, CONDA_PREFIX or PYBOMB_PREFIX if any
	make
	(sudo) make install
	sudo ldconfig # if installing as root user
	```
    
## Usage:  

    
- An example of a transmitter and a receiver can be found in gr-lora_sdr/app/single_user (both python and grc).  


    
## Frequent errors:  
- "ImportError: No module named lora_sdr":
	- This issue comes probably from missing PYTHONPATH and LD_LIBRARY_PATH                             
	- Refer to https://wiki.gnuradio.org/index.php/ModuleNotFoundError to modify those variables. If you set a prefix during the "cmake" call, skip directly to point C.(Verifying that the paths exist in your folders might help.)
- The OOT blocks doesn't appear in gnuradio-companion:	
	- The new blocks can be loaded in gnuradio-companion by adding the following lines in home/{username}/.gnuradio/config.conf (If this file doesn't exist you need to create it):

			[grc]
			local_blocks_path=path_to_the_downloaded_folder/gr-lora_sdr/grc
## Credit
This work was inspired from [https://github.com/rpp0/gr-lora](https://github.com/rpp0/gr-lora) by Pieter Robyns, Peter Quax, Wim Lamotte and William Thenaers. Which architecture and functionalities have been improved to better emulate the physical layer of LoRa. 

## Licence
Distributed under the GPL-3.0 License License. See LICENSE for more information.




	













