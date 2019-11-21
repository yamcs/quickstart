package com.example.myproject;

import java.io.IOException;
import java.util.List;

import org.yamcs.archive.IndexIterator;
import org.yamcs.archive.IndexServer;
import org.yamcs.archive.TmIndex;
import org.yamcs.protobuf.Yamcs.ArchiveRecord;
import org.yamcs.protobuf.Yamcs.NamedObjectId;
import org.yamcs.yarch.Stream;
import org.yamcs.yarch.Tuple;

/**
 * The default {@link TmIndex} implementation of {@link IndexServer} relies on time information from the secundary
 * header. We override this, because our packets don't use this header.
 */
public class NoopCompletenessIndex implements TmIndex {

    public NoopCompletenessIndex(String instance, boolean readonly) {
    }

    @Override
    public void onTuple(Stream stream, Tuple tuple) {
        // NOP
    }

    @Override
    public void close() throws IOException {
        // NOP
    }

    @Override
    public void deleteRecords(long start, long stop) {
        // NOP
    }

    @Override
    public IndexIterator getIterator(List<NamedObjectId> names, long start, long stop) {
        return new IndexIterator() {

            @Override
            public ArchiveRecord getNextRecord() {
                return null;
            }

            @Override
            public void close() {
                // NOP
            }
        };
    }
}
