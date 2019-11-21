package com.example.myproject;

import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import org.yamcs.TmPacket;
import org.yamcs.YConfiguration;
import org.yamcs.tctm.AbstractPacketPreprocessor;
import org.yamcs.utils.TimeEncoding;

public class MyPacketPreprocessor extends AbstractPacketPreprocessor {

    private Map<Integer, AtomicInteger> seqCounts = new HashMap<>();

    public MyPacketPreprocessor(String yamcsInstance) {
        super(yamcsInstance, YConfiguration.emptyConfig());
    }

    @Override
    public TmPacket process(TmPacket packet) {

        byte[] bytes = packet.getPacket();
        if (bytes.length < 6) { // Expect at least the length of CCSDS primary header
            eventProducer.sendWarning("SHORT_PACKET",
                    "Short packet received, length: " + bytes.length + "; minimum required length is 6 bytes.");

            // If we return null, the packet is dropped.
            return null;
        }

        // Verify continuity for a given APID based on the CCSDS sequence counter
        int apidseqcount = ByteBuffer.wrap(bytes).getInt(0);
        int apid = (apidseqcount >> 16) & 0x07FF;
        int seq = (apidseqcount) & 0x3FFF;
        AtomicInteger ai = seqCounts.computeIfAbsent(apid, k -> new AtomicInteger());
        int oldseq = ai.getAndSet(seq);

        if (((seq - oldseq) & 0x3FFF) != 1) {
            eventProducer.sendWarning("SEQ_COUNT_JUMP",
                    "Sequence count jump for APID: " + apid + " old seq: " + oldseq + " newseq: " + seq);
        }

        // Our custom packets don't include a secundary header with time information.
        // Use Yamcs-local time instead.
        packet.setGenerationTime(TimeEncoding.getWallclockTime());

        // Use the full 32-bits, so that both APID and the count are included.
        // Yamcs uses this attribute to uniquely identify the packet (together with the gentime)
        packet.setSequenceCount(apidseqcount);

        return packet;
    }
}
