# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An OpenFlow 1.0 L2 learning switch implementation.
"""


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

import pdb
import struct
from ryu.lib.mac import haddr_to_str as h2s
import socket

class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        #when used with vxlan, these are the src/dst HW addr of the
        #internal ports of the src, dest
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        src_mac, dest_mac, eth_type = struct.unpack_from("!6s6sH", buffer(msg.data), 0)

        #Ethernet 2
        #See: http://networkengineering.stackexchange.com/questions/5300
        if hex(eth_type) == '0x800':
            """
             +----+----+------+------+-----+
             | DA | SA | Type | Data | FCS |
             +----+----+------+------+-----+
            """
            #Get the IP header len
            offset = 14 #size of ethernet header
            #The first byte
            first, = struct.unpack_from("!B", buffer(msg.data), offset)
            header_len = first & 0b00001111 #in number of words

            offset = 14 + 9#Ethernet header + first 9 bytes of IP header
            prot, _, src_ip, dest_ip = struct.unpack_from("!B2s4s4s", buffer(msg.data), offset)
            
            src_ip = socket.inet_ntoa(src_ip)
            dest_ip = socket.inet_ntoa(dest_ip)

            OUTPUT_STR = "SRC_MAC={}, DST_MAC={}, SRC_IP={}, DST_IP={} {} ".format(h2s(src_mac), h2s(dest_mac), src_ip, dest_ip, prot)

            #self.logger.info("SRC_MAC={}, DST_MAC={}".format(h2s(src_mac), h2s(dst_mac) ))
            #Protocol Numbers
            ICMP = 1
            TCP = 6
            UDP = 17

            if prot == TCP or prot == UDP:
               offset = 14 + header_len * 4
               #get port number 
               src_port, dest_port = struct.unpack_from("!HH", buffer(msg.data), offset)
               OUTPUT_STR += "SRC_PORT={} DST_PORT={}".format(src_port, dest_port)

            
            self.logger.info(OUTPUT_STR)
#
#        else: #802.3
#            #Should be rarely seen
#            """
#             +----+----+------+------+------+------+-----+
#             | DA | SA | Len  | LLC  | SNAP | Data | FCS |
#             +----+----+------+------+------+------+-----+
#            """

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, msg.in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = msg.in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath, msg.in_port, dst, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)
